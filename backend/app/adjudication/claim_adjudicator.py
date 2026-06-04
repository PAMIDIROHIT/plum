# =====================================================================
# Adjudication - Unified Claim Adjudicator and Orchestrator
# =====================================================================

import json
import os
import random
from datetime import datetime
from typing import Dict, Any, List

from ..schemas.adjudication_schema import ClaimSubmitRequest

# Rule sub-engines
from ..rule_engine.eligibility_rules import validate_eligibility_checks
from ..rule_engine.coverage_rules import apply_coverage_concessions
from ..rule_engine.limit_rules import check_category_sub_limits
from ..rule_engine.policy_rules import check_policy_waiting_periods

# Pipelines
from ..ai_pipeline.extraction_pipeline import run_extraction_pipeline
from ..ai_pipeline.adjudication_pipeline import run_adjudication_pipeline
from ..ai_pipeline.fraud_pipeline import execute_fraud_pipeline

# Support modules
from ..adjudication.confidence_scorer import calculate_adjudication_confidence
from ..automation.workflow_engine import execute_claim_workflow

def load_adjudication_rules_text() -> str:
    """
    Loads raw adjudication rules markdown text.
    """
    public_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "public",
        "adjudication_rules.md"
    )
    if os.path.exists(public_path):
        with open(public_path, "r") as f:
            return f.read()
    
    root_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "assignment_docs",
        "adjudication_rules.md"
    )
    if os.path.exists(root_path):
        with open(root_path, "r") as f:
            return f.read()
            
    return "Execute policy compliance rules."

def run_local_adjudication_flow(claim: Dict[str, Any], policy: Dict[str, Any], ytd_approved_sum: float = 0.0) -> Dict[str, Any]:
    """
    Deterministic programmatic rule checks mapping to sub-engines.
    """
    claim_id = claim.get("claim_id") or f"CLM_{random.randint(100000, 999999)}"
    
    # Enforce YTD Annual Limit
    annual_limit = policy.get("coverage_details", {}).get("annual_limit", 999999.0)
    if ytd_approved_sum >= annual_limit:
        return {
            "claim_id": claim_id,
            "decision": "REJECTED",
            "approved_amount": 0.0,
            "rejection_reasons": ["ANNUAL_LIMIT_EXCEEDED"],
            "confidence_score": 0.98,
            "notes": f"Annual policy limit of ₹{annual_limit} has already been exhausted (YTD Approved: ₹{ytd_approved_sum}).",
            "next_steps": "No further claims can be reimbursed under this policy for the current policy year."
        }
        
    # 1. Fraud / high-frequency validations
    fraud_flags = execute_fraud_pipeline(claim)
    if len(claim.get("flags", [])) > 0 or "Multiple claims same day" in fraud_flags:
        return {
            "claim_id": claim_id,
            "decision": "MANUAL_REVIEW",
            "approved_amount": 0.0,
            "rejection_reasons": [],
            "confidence_score": 0.65,
            "flags": list(set(fraud_flags + claim.get("flags", []))),
            "notes": "Refer for manual review due to high frequency of claims submitted on the same day.",
            "next_steps": "Our claims processing team will manually verify the authenticity of these claims."
        }
        
    claim_amount = claim.get("claim_amount", 0.0)
    if claim_amount > 25000:
        return {
            "claim_id": claim_id,
            "decision": "MANUAL_REVIEW",
            "approved_amount": 0.0,
            "rejection_reasons": [],
            "confidence_score": 0.70,
            "flags": ["High-value claim"],
            "notes": "Claim amount exceeds ₹25,000, triggering mandatory manual supervisor sign-off.",
            "next_steps": "Pending verification by claims manager."
        }

    # 2. Minimum amount limit validation
    min_amount = policy["claim_requirements"]["minimum_claim_amount"]
    if claim_amount < min_amount:
        return {
            "claim_id": claim_id,
            "decision": "REJECTED",
            "approved_amount": 0.0,
            "rejection_reasons": ["BELOW_MIN_AMOUNT"],
            "confidence_score": 0.99,
            "notes": f"Claim amount ₹{claim_amount} is below the minimum threshold of ₹{min_amount}.",
            "next_steps": "Claim cannot be processed. Minimum claim amount must be at least ₹500."
        }

    # 3. Waiting period check
    waiting_status = check_policy_waiting_periods(claim, policy)
    if not waiting_status["eligible"]:
        return {
            "claim_id": claim_id,
            "decision": "REJECTED",
            "approved_amount": 0.0,
            "rejection_reasons": [waiting_status["rejection_reason"]],
            "confidence_score": 0.96,
            "notes": waiting_status["notes"],
            "next_steps": waiting_status["next_steps"]
        }

    # 4. Eligibility doc checks
    eligibility = validate_eligibility_checks(claim)
    if not eligibility["eligible"]:
        return {
            "claim_id": claim_id,
            "decision": "REJECTED",
            "approved_amount": 0.0,
            "rejection_reasons": [eligibility["rejection_reason"]],
            "confidence_score": 0.95,
            "notes": eligibility["notes"],
            "next_steps": eligibility["next_steps"]
        }

    # 5. Policy exclusions (Dynamic evaluation from policy_terms.json)
    prescription = claim.get("documents", {}).get("prescription", {})
    diagnosis_text = (prescription.get("diagnosis") or "").lower()
    treatment_text = (prescription.get("treatment") or "").lower()
    procedures_text = " ".join(prescription.get("procedures") or []).lower()
    combined_clinical_text = f"{diagnosis_text} {treatment_text} {procedures_text}"

    bill = claim.get("documents", {}).get("bill", {})

    # Detect if this is a dental/alt-medicine claim that will be handled as itemized below.
    # For those, cosmetic items are rejected line-by-line (teeth_whitening) but valid items
    # (root_canal) are still approved — so skip blanket exclusion rejection.
    has_dental_items = "root_canal" in bill or "teeth_whitening" in bill
    has_alt_items = "therapy_charges" in bill

    exclusions = policy.get("exclusions", [])
    
    # Map clinical synonyms to policy exclusions since the local engine lacks LLM semantics
    exclusion_synonyms = {
        "weight loss": ["obesity", "weight", "bariatric", "diet plan"],
        "cosmetic": ["cosmetic", "aesthetic", "beauty", "whitening", "plastic surgery"],
        "experimental": ["experimental", "unproven", "trial"],
        "infertility": ["infertility", "ivf", "fertility"]
    }

    for exclusion in exclusions:
        exclusion_lower = exclusion.lower()
        # Find matching synonym list for this policy exclusion
        keywords_to_check = [exclusion_lower.split()[0]]  # fallback to first word
        for ex_key, syns in exclusion_synonyms.items():
            if ex_key in exclusion_lower:
                keywords_to_check = syns
                break

        if any(kw in combined_clinical_text for kw in keywords_to_check):
            # For dental/alt-medicine itemized claims, cosmetic items are handled
            # line-by-line in the partial-approval section below — don't blanket-reject.
            if (exclusion_lower.startswith("cosmetic") or "whitening" in exclusion_lower) and (has_dental_items or has_alt_items):
                continue
            return {
                "claim_id": claim_id,
                "decision": "REJECTED",
                "approved_amount": 0.0,
                "rejection_reasons": ["SERVICE_NOT_COVERED"],
                "confidence_score": 0.97,
                "notes": f"Treatment matches policy exclusion: {exclusion}",
                "next_steps": f"This claim is ineligible for reimbursement because '{exclusion}' is listed in policy exclusions."
            }

    # 6. Pre-authorization check for diagnostic tests
    bill = claim.get("documents", {}).get("bill", {})
    diagnostic_details = policy.get("coverage_details", {}).get("diagnostic_tests", {})
    covered_tests = diagnostic_details.get("covered_tests", [])
    
    needs_preauth = False
    preauth_test_name = ""
    
    # Check if bill contains high-value scans that require pre-auth in the policy
    if (bill.get("mri_scan") or 0) > 0 and any("MRI" in t and "pre-auth" in t.lower() for t in covered_tests):
        needs_preauth = True
        preauth_test_name = "MRI scan"
    elif (bill.get("ct_scan") or 0) > 0 and any("CT" in t and "pre-auth" in t.lower() for t in covered_tests):
        needs_preauth = True
        preauth_test_name = "CT scan"
        
    if needs_preauth:
        return {
            "claim_id": claim_id,
            "decision": "REJECTED",
            "approved_amount": 0.0,
            "rejection_reasons": ["PRE_AUTH_MISSING"],
            "confidence_score": 0.94,
            "notes": f"{preauth_test_name} requires pre-authorization as per policy terms.",
            "next_steps": "Please submit pre-authorization certificate or refer for manual review."
        }

    # Detect claim type first (needed to decide whether to apply hard per-claim cap)
    is_network = claim.get("hospital") in policy.get("network_hospitals", [])
    cashless_request = claim.get("cashless_request", False)

    is_alternative = "therapy_charges" in bill or "alternative_medicine" in bill or "alternative" in diagnosis_text
    is_dental = "root_canal" in bill or "teeth_whitening" in bill or "dental" in diagnosis_text

    # Hard cap limit check — skip for dental/alt medicine which use itemized partial approval
    per_claim_limit = policy["coverage_details"]["per_claim_limit"]
    if claim_amount > per_claim_limit and not is_alternative and not is_dental:
        return {
            "claim_id": claim_id,
            "decision": "REJECTED",
            "approved_amount": 0.0,
            "rejection_reasons": ["PER_CLAIM_EXCEEDED"],
            "confidence_score": 0.98,
            "notes": f"Claim amount exceeds per-claim limit of ₹{per_claim_limit}",
            "next_steps": "Claims exceeding ₹5,000 per claim limit are rejected under standard policy terms."
        }

    if not is_alternative and not is_dental:
        # Determine discount percentage
        discount_pct = policy["coverage_details"]["consultation_fees"].get("network_discount", 20) / 100.0 if is_network else 0.0
        # Determine copay percentage (waived for network cashless claims)
        copay_pct = 0.0 if (is_network and cashless_request) else (policy["coverage_details"]["consultation_fees"].get("copay_percentage", 10) / 100.0)
        
        network_discount_applied = claim_amount * discount_pct
        amount_after_discount = claim_amount - network_discount_applied
        copay_applied = amount_after_discount * copay_pct
        approved_amount = amount_after_discount - copay_applied
        
        # Enforce per-claim limit
        per_claim_limit = policy["coverage_details"]["per_claim_limit"]
        if claim_amount > per_claim_limit:
            return {
                "claim_id": claim_id,
                "decision": "REJECTED",
                "approved_amount": 0.0,
                "rejection_reasons": ["PER_CLAIM_EXCEEDED"],
                "confidence_score": 0.98,
                "notes": f"Claim amount exceeds per-claim limit of ₹{per_claim_limit}",
                "next_steps": "Claims exceeding ₹5,000 per claim limit are rejected under standard policy terms."
            }
            
        return {
            "claim_id": claim_id,
            "decision": "APPROVED",
            "approved_amount": approved_amount,
            "rejection_reasons": [],
            "confidence_score": 0.93 if is_network else 0.95,
            "copay_applied": copay_applied if copay_applied > 0 else None,
            "network_discount_applied": network_discount_applied if network_discount_applied > 0 else None,
            "cashless_approved": True if (is_network and cashless_request) else None,
            "notes": "OPD claim approved with standard terms and concessions applied.",
            "next_steps": "Reimbursement will be credited to the employee's registered account." if not cashless_request else "Cashless facility authorized. Member pays zero at counter."
        }

    # Itemized processing
    temp_approved = 0.0
    is_partial = False
    rejected_items = []
    copay_applied = 0.0
    network_discount_applied = 0.0
    limits_checked = []

    # 1. Consultation fee
    if "consultation_fee" in bill:
        val = bill["consultation_fee"]
        # For specialized claims (dental/alt medicine), consultation is bundled — no copay
        if is_alternative or is_dental:
            concessions = {"approved_amount": val, "network_discount_applied": 0.0, "copay_applied": 0.0}
        else:
            concessions = apply_coverage_concessions("consultation_fees", val, policy, is_network)
        network_discount_applied += concessions["network_discount_applied"]
        copay_applied += concessions["copay_applied"]
        
        limit_check = check_category_sub_limits("consultation_fee", val, concessions["approved_amount"], policy)
        if limit_check["is_exceeded"]:
            is_partial = True
            rejected_items.append(limit_check["rejection_detail"])
        temp_approved += limit_check["approved_amount"]
        limits_checked.append({"category": "Consultation", "limit": limit_check["sub_limit"], "claimed": val, "approved": limit_check["approved_amount"]})

    # 2. Pharmacy
    if "medicines" in bill:
        val = bill["medicines"]
        concessions = apply_coverage_concessions("pharmacy", val, policy, is_network)
        limit_check = check_category_sub_limits("medicines", val, concessions["approved_amount"], policy)
        if limit_check["is_exceeded"]:
            is_partial = True
            rejected_items.append(limit_check["rejection_detail"])
        temp_approved += limit_check["approved_amount"]
        limits_checked.append({"category": "Pharmacy", "limit": limit_check["sub_limit"], "claimed": val, "approved": limit_check["approved_amount"]})

    # 3. Dental
    if "root_canal" in bill or "teeth_whitening" in bill:
        limit = policy["coverage_details"]["dental"]["sub_limit"]
        claimed = 0.0
        approved = 0.0
        
        if "root_canal" in bill:
            claimed += bill["root_canal"]
            approved += bill["root_canal"]
        if "teeth_whitening" in bill:
            claimed += bill["teeth_whitening"]
            is_partial = True
            rejected_items.append("Teeth whitening - cosmetic procedure")
            
        limit_check = check_category_sub_limits("dental", claimed, approved, policy)
        if limit_check["is_exceeded"]:
            is_partial = True
            rejected_items.append(limit_check["rejection_detail"])
        temp_approved += limit_check["approved_amount"]
        limits_checked.append({"category": "Dental", "limit": limit_check["sub_limit"], "claimed": claimed, "approved": limit_check["approved_amount"]})

    # 4. Alternative Medicine
    if "therapy_charges" in bill:
        val = bill["therapy_charges"]
        limit_check = check_category_sub_limits("therapy_charges", val, val, policy)
        if limit_check["is_exceeded"]:
            is_partial = True
            rejected_items.append(limit_check["rejection_detail"])
        temp_approved += limit_check["approved_amount"]
        limits_checked.append({"category": "Alternative Medicine", "limit": limit_check["sub_limit"], "claimed": val, "approved": limit_check["approved_amount"]})

    approved_amount = max(0.0, temp_approved)
    
    # Enforce remaining YTD annual limit capping
    remaining_limit = max(0.0, annual_limit - ytd_approved_sum)
    if approved_amount > remaining_limit:
        approved_amount = remaining_limit
        is_partial = True
        rejected_items.append(f"Cap applied: exceeds annual policy remaining limit of ₹{remaining_limit}")

    if approved_amount == 0.0:
        return {
            "claim_id": claim_id,
            "decision": "REJECTED",
            "approved_amount": 0.0,
            "rejection_reasons": ["SERVICE_NOT_COVERED"] if ytd_approved_sum < annual_limit else ["ANNUAL_LIMIT_EXCEEDED"],
            "confidence_score": 0.9,
            "notes": "None of the submitted items are eligible under policy benefits or annual limit is exhausted.",
            "next_steps": "Please consult the policy document for covered services, remaining sub-limits, and YTD balances."
        }

    decision = "PARTIAL" if is_partial else "APPROVED"
    return {
        "claim_id": claim_id,
        "decision": decision,
        "approved_amount": approved_amount,
        "rejection_reasons": [],
        "rejected_items": rejected_items if len(rejected_items) > 0 else None,
        "confidence_score": 0.92 if is_partial else 0.95,
        "copay_applied": copay_applied if copay_applied > 0 else None,
        "network_discount_applied": network_discount_applied if network_discount_applied > 0 else None,
        "limits_checked": limits_checked,
        "notes": f"Claim {decision.lower()} successfully."
    }

def process_and_adjudicate_claim(claim_req: ClaimSubmitRequest, policy: dict, db: Any) -> dict:
    """
    Unified Orchestrator: OCR extraction -> DeepSeek R1 adjudication -> SQLite persistence
    """
    combined_docs = f"""
=== PRESCRIPTION DOCUMENT ===
{claim_req.prescription_text}

=== BILL/INVOICE DOCUMENT ===
{claim_req.bill_text}
"""
    # 1. OCR Extraction — use prior upload-time extraction if provided (Single Source of Truth).
    # This prevents field mutation: doctor_reg, diagnosis, medicines remain identical
    # to what was shown in the upload preview.
    if claim_req.prior_gemini_extraction:
        extracted = claim_req.prior_gemini_extraction
        print(f"[Adjudicator] Reusing upload-time Gemini extraction (skipping re-extraction).")
    else:
        extracted = run_extraction_pipeline(combined_docs)
        print(f"[Adjudicator] Fresh extraction run (no prior extraction provided).")

    member_name = claim_req.member_name or extracted.get("patient_name") or "John Doe"
    # Fix: Python `or` treats 0.0 as falsy — use explicit check so user-provided amount is always respected
    if claim_req.claim_amount is not None and claim_req.claim_amount > 0:
        claim_amount = float(claim_req.claim_amount)
    else:
        claim_amount = float(extracted.get("claim_amount") or 0.0)
        
    extracted["claim_amount"] = claim_amount

    # Calculate YTD Approved amount for the member in the current treatment date's year
    treatment_year = datetime.now().year
    if claim_req.treatment_date:
        try:
            treatment_year = datetime.strptime(claim_req.treatment_date, "%Y-%m-%d").year
        except Exception:
            pass

    prior_claims = db.claims.find({
        "member_id": claim_req.member_id,
        "decision": {"$in": ["APPROVED", "PARTIAL"]}
    })

    ytd_approved_sum = 0.0
    for pc in prior_claims:
        try:
            pc_year = datetime.strptime(pc.get("treatment_date", ""), "%Y-%m-%d").year
            if pc_year == treatment_year:
                ytd_approved_sum += pc.get("approved_amount", 0.0)
        except Exception:
            pass

    # Construct full claim payload to be used by either AI or Local engines
    claim_payload = {
        "claim_amount": claim_amount,
        "member_name": member_name,
        "member_id": claim_req.member_id,
        "member_join_date": claim_req.member_join_date,
        "treatment_date": claim_req.treatment_date,
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

    decision_data = {}

    # 2. Decision Routing
    if claim_req.adjudication_mode == "ai":
        rules_text = load_adjudication_rules_text()
        ds_verdict = run_adjudication_pipeline(claim_payload, policy, rules_text)
        
        decision_data = {
            "decision": ds_verdict.get("decision", "MANUAL_REVIEW"),
            "approved_amount": ds_verdict.get("approved_amount", 0.0),
            "rejection_reasons": ds_verdict.get("rejection_reasons", []),
            "confidence_score": ds_verdict.get("confidence_score", 0.95),
            "notes": " ".join(ds_verdict.get("reasoning", [])) or ds_verdict.get("next_steps", "DeepSeek R1 reasoning executed."),
            "next_steps": ds_verdict.get("next_steps", "Pending Action."),
            "meta": ds_verdict
        }

        # Enforce YTD Annual Limit for AI Verdicts
        annual_limit = policy.get("coverage_details", {}).get("annual_limit", 999999.0)
        remaining_limit = max(0.0, annual_limit - ytd_approved_sum)
        
        if remaining_limit <= 0.0:
            decision_data["decision"] = "REJECTED"
            decision_data["approved_amount"] = 0.0
            decision_data["rejection_reasons"] = list(set(decision_data.get("rejection_reasons", []) + ["ANNUAL_LIMIT_EXCEEDED"]))
            decision_data["notes"] = f"Annual policy limit of ₹{annual_limit} exhausted. YTD Approved: ₹{ytd_approved_sum}."
        elif decision_data.get("approved_amount", 0.0) > remaining_limit:
            decision_data["approved_amount"] = remaining_limit
            if decision_data["decision"] == "APPROVED":
                decision_data["decision"] = "PARTIAL"
            decision_data["notes"] = decision_data.get("notes", "") + f" | Cap applied: exceeds remaining annual policy limit of ₹{remaining_limit}."
    else:
        # Local Rules engine
        outcome = run_local_adjudication_flow(claim_payload, policy, ytd_approved_sum)
        
        decision_data = {
            "decision": outcome.get("decision", "APPROVED"),
            "approved_amount": outcome.get("approved_amount", 0.0),
            "rejection_reasons": outcome.get("rejection_reasons", []),
            "confidence_score": outcome.get("confidence_score", 0.95),
            "notes": outcome.get("notes") or "Adjudicated locally by system rules.",
            "next_steps": outcome.get("next_steps") or "Review details on dashboard.",
            "meta": outcome
        }

    # 3. Compute final confidence score via multi-factor scorer
    claim_payload_for_scoring = {
        "member_id": claim_req.member_id,
        "treatment_date": claim_req.treatment_date,
        "documents": {
            "prescription": {
                "doctor_reg": extracted.get("doctor_registration_number", "")
            }
        }
    }
    final_confidence = calculate_adjudication_confidence(
        meta=decision_data,
        extraction_data=extracted,
        claim=claim_payload_for_scoring
    )
    decision_data["confidence_score"] = final_confidence

    # 4. Determine workflow state
    workflow_ctx = execute_claim_workflow(decision_data)
    meta_with_workflow = {**decision_data.get("meta", {}), "workflow": workflow_ctx}

    # 5. DB Persistence (Normalized MongoDB Architecture)
    claim_id = decision_data.get("meta", {}).get("claim_id") or (
            f"CLM_{claim_req.member_id}_{claim_req.treatment_date}_{datetime.now().strftime('%H%M%S%f')}"
        )
    created_at = datetime.now().isoformat()
        
    # Collection 1: claims
    db_claim = {
        "claim_id": claim_id,
        "member_id": claim_req.member_id,
        "member_name": member_name,
        "treatment_date": claim_req.treatment_date,
        "claim_amount": claim_amount,
        "approved_amount": decision_data.get("approved_amount", 0.0),
        "decision": decision_data.get("decision", "MANUAL_REVIEW"),
        "confidence_score": final_confidence,
        "created_at": created_at
    }
    db.claims.insert_one(db_claim)

    # Collection 2: documents
    db.documents.insert_one({
        "claim_id": claim_id,
        "member_id": claim_req.member_id,
        "extraction_data": extracted,
        "created_at": created_at
    })

    # Collection 3: adjudication_logs
    db.adjudication_logs.insert_one({
        "claim_id": claim_id,
        "rejection_reasons": decision_data.get("rejection_reasons", []),
        "notes": decision_data.get("notes", ""),
        "next_steps": decision_data.get("next_steps", ""),
        "adjudication_meta": meta_with_workflow,
        "created_at": created_at
    })

    # Collection 4: members (Upsert)
    db.members.update_one(
        {"member_id": claim_req.member_id},
        {"$set": {"member_name": member_name, "last_active": created_at}},
        upsert=True
    )

    # Collection 5: fraud_flags (Only if anomalies exist or low confidence)
    fraud_flags = decision_data.get("meta", {}).get("fraud_flags") or decision_data.get("meta", {}).get("flags", [])
    if fraud_flags or final_confidence < 0.7:
        db.fraud_flags.insert_one({
            "claim_id": claim_id,
            "member_id": claim_req.member_id,
            "flags": fraud_flags,
            "confidence_score": final_confidence,
            "workflow_state": workflow_ctx.get("workflow_state"),
            "created_at": created_at
        })


    # Build extraction_data for frontend display (Gemini-extracted fields)
    extraction_data = {
        "patient_name": extracted.get("patient_name"),
        "doctor_name": extracted.get("doctor_name"),
        "doctor_registration_number": extracted.get("doctor_registration_number"),
        "hospital_or_clinic": extracted.get("hospital_or_clinic"),
        "diagnosis": extracted.get("diagnosis"),
        "medicines": extracted.get("medicines"),
        "tests_prescribed": extracted.get("tests_prescribed"),
        "procedures": extracted.get("procedures"),
        "bill_breakdown": extracted.get("bill_breakdown"),
        "treatment_date": extracted.get("treatment_date"),
        "ocr_confidence": extracted.get("ocr_confidence"),
        "extraction_confidence": extracted.get("extraction_confidence"),
        "document_types": extracted.get("document_types"),
        "possible_fraud_flags": extracted.get("possible_fraud_flags"),
        "document_issues": extracted.get("document_issues"),
        "missing_documents": extracted.get("missing_documents"),
    }

    return {
        "claim_id": db_claim["claim_id"],
        "decision": db_claim["decision"],
        "approved_amount": db_claim["approved_amount"],
        "claim_amount": claim_amount,
        "rejection_reasons": decision_data.get("rejection_reasons", []),
        "confidence_score": final_confidence,
        "notes": decision_data.get("notes", ""),
        "next_steps": decision_data.get("next_steps", ""),
        "workflow_state": workflow_ctx.get("workflow_state"),
        "workflow_description": workflow_ctx.get("state_description"),
        "copay_applied": decision_data.get("meta", {}).get("copay_applied") or decision_data.get("meta", {}).get("deductions", {}).get("copay"),
        "network_discount_applied": decision_data.get("meta", {}).get("network_discount_applied") or decision_data.get("meta", {}).get("network_discount"),
        "rejected_items": decision_data.get("meta", {}).get("rejected_items"),
        "approved_items": decision_data.get("meta", {}).get("approved_items"),
        "policy_violations": decision_data.get("meta", {}).get("policy_violations"),
        "flags": decision_data.get("meta", {}).get("fraud_flags") or decision_data.get("meta", {}).get("flags"),
        "medical_necessity_analysis": decision_data.get("meta", {}).get("medical_necessity_analysis"),
        "reasoning": decision_data.get("meta", {}).get("reasoning"),
        "extraction_data": extraction_data,
    }
