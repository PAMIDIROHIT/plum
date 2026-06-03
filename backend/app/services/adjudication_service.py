import json
import os
from sqlalchemy.orm import Session
from ..models.claim import ClaimModel
from ..schemas.claim_schema import ClaimSubmitRequest
from .gemini_service import run_gemini_ocr
from .deepseek_service import run_deepseek_adjudication
from .rule_engine import adjudicate_claim_local

def load_adjudication_rules_text() -> str:
    """
    Loads raw adjudication rules markdown text.
    """
    public_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "public", "adjudication_rules.md")
    if os.path.exists(public_path):
        with open(public_path, "r") as f:
            return f.read()
    
    root_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "adjudication_rules.md")
    if os.path.exists(root_path):
        with open(root_path, "r") as f:
            return f.read()
            
    return "Execute policy compliance rules."

def process_and_adjudicate_claim(claim_req: ClaimSubmitRequest, policy: dict, db: Session) -> dict:
    """
    Unified claims adjudication workflow coordinator.
    Step 1: Runs Gemini 2.5 Flash OCR text parsing.
    Step 2: Runs DeepSeek R1 policy reasoning (or local rules engine).
    Step 3: Persists the claim records in the database.
    """
    combined_docs = f"""
=== PRESCRIPTION DOCUMENT ===
{claim_req.prescription_text}

=== BILL/INVOICE DOCUMENT ===
{claim_req.bill_text}
"""

    # 1. OCR Extractions
    extracted = run_gemini_ocr(combined_docs)
    
    # Fill clinic/demographics if missed in raw form
    member_name = claim_req.member_name or extracted.get("patient_name", "John Doe")
    claim_amount = claim_req.claim_amount or extracted.get("claim_amount", 0.0)

    decision_data = {}
    
    # 2. Adjudication Routing
    if claim_req.adjudication_mode == "ai":
        rules_text = load_adjudication_rules_text()
        ds_verdict = run_deepseek_adjudication(extracted, policy, rules_text)
        
        decision_data = {
            "decision": ds_verdict.get("decision", "MANUAL_REVIEW"),
            "approved_amount": ds_verdict.get("approved_amount", 0.0),
            "rejection_reasons": ds_verdict.get("rejection_reasons", []),
            "confidence_score": ds_verdict.get("confidence_score", 0.95),
            "notes": " ".join(ds_verdict.get("reasoning", [])) or ds_verdict.get("next_steps", "DeepSeek R1 reasoning executed."),
            "next_steps": ds_verdict.get("next_steps", "Pending Action."),
            "meta": ds_verdict
        }
    else:
        # Local Rules Engine
        claim_payload = {
            "claim_amount": claim_amount,
            "member_name": member_name,
            "member_id": claim_req.member_id,
            "hospital": claim_req.hospital,
            "cashless_request": claim_req.cashless_request,
            "previous_claims_same_day": claim_req.previous_claims_same_day,
            "documents": {
                "prescription": {
                    "doctor_name": extracted.get("doctor_name", ""),
                    "doctor_reg": extracted.get("doctor_registration_number", ""),
                    "diagnosis": extracted.get("diagnosis", ""),
                    "medicines_prescribed": extracted.get("medicines"),
                    "procedures": extracted.get("procedures")
                },
                "bill": extracted.get("bill_breakdown", {})
            }
        }
        
        outcome = adjudicate_claim_local(claim_payload, policy)
        
        decision_data = {
            "decision": outcome.get("decision", "APPROVED"),
            "approved_amount": outcome.get("approved_amount", 0.0),
            "rejection_reasons": outcome.get("rejection_reasons", []),
            "confidence_score": outcome.get("confidence_score", 0.95),
            "notes": outcome.get("notes") or "Adjudicated locally by system rules.",
            "next_steps": outcome.get("next_steps") or "Review details on dashboard.",
            "meta": outcome
        }

    # 3. SQLite DB Persistence
    db_claim = ClaimModel(
        claim_id=decision_data.get("meta", {}).get("claim_id") or f"CLM_{claim_req.member_id}_{claim_req.treatment_date}",
        member_id=claim_req.member_id,
        member_name=member_name,
        treatment_date=claim_req.treatment_date,
        claim_amount=claim_amount,
        approved_amount=decision_data.get("approved_amount", 0.0),
        decision=decision_data.get("decision", "MANUAL_REVIEW"),
        rejection_reasons=json.dumps(decision_data.get("rejection_reasons", [])),
        notes=decision_data.get("notes", ""),
        next_steps=decision_data.get("next_steps", ""),
        raw_input=json.dumps(extracted),
        adjudication_meta=json.dumps(decision_data.get("meta", {}))
    )
    
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    
    # Return formatted schema payload for Next.js UI rendering
    return {
        "claim_id": db_claim.claim_id,
        "decision": db_claim.decision,
        "approved_amount": db_claim.approved_amount,
        "rejection_reasons": json.loads(db_claim.rejection_reasons),
        "confidence_score": decision_data.get("confidence_score", 0.95),
        "notes": db_claim.notes,
        "next_steps": db_claim.next_steps,
        "copay_applied": decision_data.get("meta", {}).get("copay_applied") or decision_data.get("meta", {}).get("deductions", {}).get("copay"),
        "network_discount_applied": decision_data.get("meta", {}).get("network_discount_applied") or decision_data.get("meta", {}).get("network_discount"),
        "rejected_items": decision_data.get("meta", {}).get("rejected_items"),
        "approved_items": decision_data.get("meta", {}).get("approved_items"),
        "policy_violations": decision_data.get("meta", {}).get("policy_violations"),
        "flags": decision_data.get("meta", {}).get("fraud_flags") or decision_data.get("meta", {}).get("flags"),
        "medical_necessity_analysis": decision_data.get("meta", {}).get("medical_necessity_analysis"),
        "reasoning": decision_data.get("meta", {}).get("reasoning")
    }
