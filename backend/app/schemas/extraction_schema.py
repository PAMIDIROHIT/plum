# =====================================================================
# Schemas - OCR Extraction Schema
# =====================================================================

from pydantic import BaseModel
from typing import List, Optional, Dict

class ExtractionSchema(BaseModel):
    """
    Pydantic schema representing the structured OCR data fields extracted by Gemini.
    """
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_registration_number: Optional[str] = None
    hospital_or_clinic: Optional[str] = None
    claim_amount: Optional[float] = 0.0
    bill_breakdown: Optional[Dict[str, float]] = {}
