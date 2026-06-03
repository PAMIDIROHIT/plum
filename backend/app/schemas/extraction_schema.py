from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class GeminiExtractionResponse(BaseModel):
    """
    Pydantic schema representing the exact JSON structure Gemini 2.5 Flash
    is prompted to return.
    """
    document_types: List[str]
    patient_name: str
    patient_age: str
    patient_gender: str
    doctor_name: str
    doctor_registration_number: str
    hospital_or_clinic: str
    treatment_date: str
    consultation_date: str
    invoice_numbers: List[str]
    diagnosis: str
    medicines: List[str]
    tests_prescribed: List[str]
    procedures: List[str]
    bill_breakdown: Dict[str, Any]
    claim_amount: float
    payment_mode: str
    documents_detected: List[str]
    missing_documents: List[str]
    document_issues: List[str]
    date_mismatches: List[str]
    authenticity_flags: List[str]
    possible_fraud_flags: List[str]
    ocr_quality_issues: List[str]
    ocr_confidence: float
    extraction_confidence: float
