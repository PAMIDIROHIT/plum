# =====================================================================
# API Routes - Claim Adjudication Blueprint
# =====================================================================

import json
import os
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from ...database.session import get_db
from ...schemas.adjudication_schema import ClaimSubmitRequest
from ...adjudication.claim_adjudicator import process_and_adjudicate_claim, run_local_adjudication_flow

router = APIRouter()

# Determine project workspace root directory (5 levels up from adjudication.py)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


# Schema for updating review decisions
class ManualReviewUpdateRequest(BaseModel):
    claim_id: str
    decision: str
    notes: str

def load_policy_config() -> dict:
    """
    Loads active policy configuration, looking for dynamically saved version first,
    then falling back to default terms.
    """
    dynamic_path = os.path.join(ROOT_DIR, "backend", "app", "db", "policy_config.json")
    if os.path.exists(dynamic_path):
        with open(dynamic_path, "r") as f:
            return json.load(f)

    policy_path = os.path.join(ROOT_DIR, "assignment_docs", "policy_terms.json")
    if os.path.exists(policy_path):
        with open(policy_path, "r") as f:
            return json.load(f)
            
    # Fallback to copy in public
    public_path = os.path.join(ROOT_DIR, "frontend", "public", "policy_terms.json")
    if os.path.exists(public_path):
        with open(public_path, "r") as f:
            return json.load(f)
            
    raise Exception("Policy terms configuration not found.")

@router.post("/submit")
def submit_claim(claim_req: ClaimSubmitRequest, db: Any = Depends(get_db)):
    """
    API endpoint to submit and process a claim document.
    Runs OCR + rules engines and saves results to MongoDB.
    """
    try:
        policy = load_policy_config()
        result = process_and_adjudicate_claim(claim_req, policy, db)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def get_claims_history(db: Any = Depends(get_db)):
    """
    Returns list of all claims logs using MongoDB Aggregation across 5 collections.
    """
    pipeline = [
        {"$sort": {"created_at": -1}},
        {
            "$lookup": {
                "from": "documents",
                "localField": "claim_id",
                "foreignField": "claim_id",
                "as": "docs"
            }
        },
        {
            "$lookup": {
                "from": "adjudication_logs",
                "localField": "claim_id",
                "foreignField": "claim_id",
                "as": "logs"
            }
        },
        {
            "$lookup": {
                "from": "fraud_flags",
                "localField": "claim_id",
                "foreignField": "claim_id",
                "as": "fraud"
            }
        }
    ]
    
    claims = list(db.claims.aggregate(pipeline))
    history = []
    
    for claim in claims:
        docs_arr = claim.get("docs", [])
        raw_input = docs_arr[0].get("extraction_data", {}) if docs_arr else {}
        
        logs_arr = claim.get("logs", [])
        log_data = logs_arr[0] if logs_arr else {}
        meta = log_data.get("adjudication_meta", {})
        
        fraud_arr = claim.get("fraud", [])
        fraud_data = fraud_arr[0] if fraud_arr else {}
        fraud_flags = fraud_data.get("flags", [])
        
        # Extract Gemini-extracted fields stored in raw_input
        extraction_data = {
            "patient_name": raw_input.get("patient_name"),
            "doctor_name": raw_input.get("doctor_name"),
            "doctor_registration_number": raw_input.get("doctor_registration_number"),
            "hospital_or_clinic": raw_input.get("hospital_or_clinic"),
            "diagnosis": raw_input.get("diagnosis"),
            "medicines": raw_input.get("medicines"),
            "tests_prescribed": raw_input.get("tests_prescribed"),
            "procedures": raw_input.get("procedures"),
            "bill_breakdown": raw_input.get("bill_breakdown"),
            "treatment_date": raw_input.get("treatment_date"),
            "ocr_confidence": raw_input.get("ocr_confidence"),
            "extraction_confidence": raw_input.get("extraction_confidence"),
            "document_types": raw_input.get("document_types"),
            "possible_fraud_flags": raw_input.get("possible_fraud_flags"),
        }
        
        rejection_reasons = log_data.get("rejection_reasons", [])
        
        history.append({
            "claim_id": claim.get("claim_id"),
            "member_id": claim.get("member_id"),
            "member_name": claim.get("member_name"),
            "treatment_date": claim.get("treatment_date"),
            "claim_amount": claim.get("claim_amount"),
            "approved_amount": claim.get("approved_amount"),
            "decision": claim.get("decision"),
            "rejection_reasons": rejection_reasons,
            "notes": log_data.get("notes", ""),
            "next_steps": log_data.get("next_steps", ""),
            "copay_applied": meta.get("copay_applied") or meta.get("deductions", {}).get("copay"),
            "network_discount_applied": meta.get("network_discount_applied") or meta.get("network_discount"),
            "rejected_items": meta.get("rejected_items"),
            "approved_items": meta.get("approved_items"),
            "policy_violations": meta.get("policy_violations"),
            "flags": fraud_flags or meta.get("fraud_flags") or meta.get("flags"),
            "medical_necessity_analysis": meta.get("medical_necessity_analysis"),
            "reasoning": meta.get("reasoning"),
            "confidence_score": claim.get("confidence_score", 0.95),
            "extraction_data": extraction_data,
            "input": {
                "member_id": claim.get("member_id"),
                "member_name": claim.get("member_name"),
                "treatment_date": claim.get("treatment_date"),
                "claim_amount": claim.get("claim_amount"),
                "hospital": raw_input.get("hospital_or_clinic")
            }
        })
        
    return history


@router.post("/review")
def update_manual_review_status(review_req: ManualReviewUpdateRequest, db: Any = Depends(get_db)):
    """
    Allows claim managers to override status details for flagged manual review claims.
    """
    claim = db.claims.find_one({"claim_id": review_req.claim_id})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim record not found.")
        
    new_notes = f"{claim.get('notes', '')} | Manual Review Note: {review_req.notes}"
    new_steps = (
        "Claim manually approved. Reimbursement processing initiated."
        if review_req.decision == "APPROVED"
        else "Claim manually rejected. Notification sent to member."
    )
    
    # Update serialized meta
    meta = json.loads(claim.get("adjudication_meta", "{}")) if isinstance(claim.get("adjudication_meta"), str) else claim.get("adjudication_meta", {})
    meta["decision"] = review_req.decision
    meta["reasoning"] = meta.get("reasoning", []) + [review_req.notes]
    
    db.claims.update_one(
        {"claim_id": review_req.claim_id},
        {"$set": {
            "decision": review_req.decision,
            "notes": new_notes,
            "next_steps": new_steps,
            "adjudication_meta": json.dumps(meta)
        }}
    )
    
    return {"status": "success", "claim_id": review_req.claim_id, "decision": review_req.decision}

@router.get("/policy")
def get_policy():
    """
    GET endpoint to retrieve the active policy configuration.
    """
    try:
        policy = load_policy_config()
        return policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/policy")
def update_policy(policy_data: Dict[str, Any]):
    """
    POST endpoint to save/update the active policy configuration.
    """
    try:
        dynamic_dir = os.path.join(ROOT_DIR, "backend", "app", "db")
        os.makedirs(dynamic_dir, exist_ok=True)
        dynamic_path = os.path.join(dynamic_dir, "policy_config.json")
        
        with open(dynamic_path, "w") as f:
            json.dump(policy_data, f, indent=2)
            
        return {"status": "success", "message": "Policy updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-cases")
def get_test_cases():
    """
    GET endpoint to retrieve mock test cases for the frontend test runner.
    """
    try:
        test_cases_path = os.path.join(ROOT_DIR, "assignment_docs", "test_cases.json")
        if os.path.exists(test_cases_path):
            with open(test_cases_path, "r") as f:
                return json.load(f)
        raise HTTPException(status_code=404, detail="Test cases file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-test")
def run_test_case(test_case_payload: Dict[str, Any]):
    """
    Runs a single structured test case from test_cases.json against the active policy.
    """
    try:
        policy = load_policy_config()
        input_data = test_case_payload.get("input_data", {})
        
        # Format payload fields to match what adjudicate_claim_local expects
        claim_payload = {
            "claim_amount": float(input_data.get("claim_amount", 0.0)),
            "member_name": input_data.get("member_name", "John Doe"),
            "member_id": input_data.get("member_id", "EMP101"),
            "member_join_date": input_data.get("member_join_date"),
            "treatment_date": input_data.get("treatment_date", "2024-01-01"),
            "hospital": input_data.get("hospital"),
            "cashless_request": bool(input_data.get("cashless_request", False)),
            "previous_claims_same_day": int(input_data.get("previous_claims_same_day", 0)),
            "documents": input_data.get("documents", {})
        }
        
        outcome = run_local_adjudication_flow(claim_payload, policy)
        
        return {
            "case_id": test_case_payload.get("case_id"),
            "case_name": test_case_payload.get("case_name"),
            "decision": outcome.get("decision", "REJECTED"),
            "approved_amount": outcome.get("approved_amount", 0.0),
            "rejection_reasons": outcome.get("rejection_reasons", []),
            "copay_applied": outcome.get("copay_applied") or outcome.get("deductions", {}).get("copay"),
            "network_discount_applied": outcome.get("network_discount_applied") or outcome.get("network_discount"),
            "rejected_items": outcome.get("rejected_items"),
            "flags": outcome.get("flags") or outcome.get("fraud_flags"),
            "notes": outcome.get("notes") or "Test case run completed."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
