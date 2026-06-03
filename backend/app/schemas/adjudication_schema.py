# =====================================================================
# Schemas - Claim Adjudication Input Schema
# =====================================================================

from pydantic import BaseModel
from typing import Optional

class ClaimSubmitRequest(BaseModel):
    """
    Pydantic schema representing the raw claim payload submitted by the client.
    Contains demographic, provider, financial info, and raw document strings.
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
    adjudication_mode: Optional[str] = "ai" # "ai" or "local"
