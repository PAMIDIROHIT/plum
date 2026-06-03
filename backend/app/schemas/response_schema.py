# =====================================================================
# Schemas - Claim Adjudication Response Schema
# =====================================================================

from pydantic import BaseModel
from typing import List, Optional

class AdjudicationResponse(BaseModel):
    """
    Pydantic schema representing the processed adjudication result returned to client.
    """
    claim_id: str
    decision: str # e.g. "APPROVED", "REJECTED", "PARTIAL", "MANUAL_REVIEW"
    approved_amount: float
    rejection_reasons: List[str]
    notes: Optional[str] = ""
    next_steps: Optional[str] = ""
