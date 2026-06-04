# =====================================================================
# Schemas - Claim Adjudication Input Schema
# =====================================================================

from pydantic import BaseModel
from typing import Optional, Dict, Any

class ClaimSubmitRequest(BaseModel):
    """
    Pydantic schema representing the raw claim payload submitted by the client.
    Contains demographic, provider, financial info, and raw document strings.
    
    prior_gemini_extraction: If provided, the backend reuses this extraction dict
    from the upload step instead of re-running Gemini/OCR extraction. This ensures
    a single source of truth and prevents field mutation between upload and submit.
    """
    member_id: str
    member_name: str
    member_join_date: Optional[str] = "2024-01-01"
    treatment_date: str
    claim_amount: float
    hospital: Optional[str] = None
    cashless_request: Optional[bool] = False
    previous_claims_same_day: Optional[int] = 0
    prescription_text: Optional[str] = ""
    bill_text: Optional[str] = ""
    adjudication_mode: Optional[str] = "ai"  # "ai" or "local"
    prior_gemini_extraction: Optional[Dict[str, Any]] = None  # Upload-time extraction passthrough
