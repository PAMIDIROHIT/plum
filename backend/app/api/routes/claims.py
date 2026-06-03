import json
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from ...db.session import get_db
from ...models.claim import ClaimModel
from ...schemas.claim_schema import ClaimSubmitRequest
from ...services.adjudication_service import process_and_adjudicate_claim

router = APIRouter()

# Schema for updating review decisions
class ManualReviewUpdateRequest(BaseModel):
    claim_id: str
    decision: str
    notes: str

def load_policy_config() -> dict:
    """
    Loads default active policy configuration from assignment_docs directory.
    """
    policy_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "assignment_docs",
        "policy_terms.json"
    )
    if os.path.exists(policy_path):
        with open(policy_path, "r") as f:
            return json.load(f)
            
    # Fallback to copy in public
    public_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "public",
        "policy_terms.json"
    )
    if os.path.exists(public_path):
        with open(public_path, "r") as f:
            return json.load(f)
            
    raise Exception("Policy terms configuration not found.")

@router.post("/submit")
def submit_claim(claim_req: ClaimSubmitRequest, db: Session = Depends(get_db)):
    """
    API endpoint to submit and process a claim document.
    Runs OCR + rules engines and saves results to SQLite DB.
    """
    try:
        policy = load_policy_config()
        result = process_and_adjudicate_claim(claim_req, policy, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def get_claims_history(db: Session = Depends(get_db)):
    """
    Returns list of all claims logs from SQLite DB.
    """
    claims = db.query(ClaimModel).order_by(ClaimModel.id.desc()).all()
    history = []
    
    for claim in claims:
        # Load metadata and JSON columns
        meta = json.loads(claim.adjudication_meta) if claim.adjudication_meta else {}
        raw_input = json.loads(claim.raw_input) if claim.raw_input else {}
        
        history.append({
            "claim_id": claim.claim_id,
            "member_id": claim.member_id,
            "member_name": claim.member_name,
            "treatment_date": claim.treatment_date,
            "claim_amount": claim.claim_amount,
            "approved_amount": claim.approved_amount,
            "decision": claim.decision,
            "rejection_reasons": json.loads(claim.rejection_reasons) if claim.rejection_reasons else [],
            "notes": claim.notes,
            "next_steps": claim.next_steps,
            "copay_applied": meta.get("copay_applied") or meta.get("deductions", {}).get("copay"),
            "network_discount_applied": meta.get("network_discount_applied") or meta.get("network_discount"),
            "rejected_items": meta.get("rejected_items"),
            "approved_items": meta.get("approved_items"),
            "policy_violations": meta.get("policy_violations"),
            "flags": meta.get("fraud_flags") or meta.get("flags"),
            "medical_necessity_analysis": meta.get("medical_necessity_analysis"),
            "reasoning": meta.get("reasoning"),
            "confidence_score": meta.get("confidence_score", 0.95),
            "input": {
                "member_id": claim.member_id,
                "member_name": claim.member_name,
                "treatment_date": claim.treatment_date,
                "claim_amount": claim.claim_amount,
                "hospital": raw_input.get("hospital_or_clinic")
            }
        })
        
    return history

@router.post("/review")
def update_manual_review_status(review_req: ManualReviewUpdateRequest, db: Session = Depends(get_db)):
    """
    Allows claim managers to override status details for flagged manual review claims.
    """
    claim = db.query(ClaimModel).filter(ClaimModel.claim_id == review_req.claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim record not found.")
        
    claim.decision = review_req.decision
    claim.notes = f"{claim.notes} | Manual Review Note: {review_req.notes}"
    claim.next_steps = (
        "Claim manually approved. Reimbursement processing initiated."
        if review_req.decision == "APPROVED"
        else "Claim manually rejected. Notification sent to member."
    )
    
    # Update serialized meta
    meta = json.loads(claim.adjudication_meta) if claim.adjudication_meta else {}
    meta["decision"] = review_req.decision
    meta["reasoning"] = meta.get("reasoning", []) + [review_req.notes]
    claim.adjudication_meta = json.dumps(meta)
    
    db.commit()
    db.refresh(claim)
    
    return {"status": "success", "claim_id": claim.claim_id, "decision": claim.decision}
