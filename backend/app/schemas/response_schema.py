from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class DeepSeekAdjudicationResponse(BaseModel):
    """
    Pydantic schema representing the exact JSON structure DeepSeek R1
    is prompted to return.
    """
    decision: str
    approved_amount: float
    deductions: Dict[str, Any]
    rejection_reasons: List[str]
    policy_violations: List[str]
    approved_items: List[str]
    rejected_items: List[str]
    fraud_flags: List[str]
    medical_necessity_analysis: List[str]
    reasoning: List[str]
    confidence_score: float
    next_steps: str
