# =====================================================================
# AI Pipeline - OCR and Information Extraction Coordinator
# =====================================================================

import re
from datetime import datetime
from typing import Dict, Any, Optional
from ..llm.prompt_manager import load_prompt_by_name
from ..llm.gemini_client import call_gemini_api
from ..document_processing.document_classifier import parse_prescription_regex, parse_bill_regex


def _extract_patient_name(text: str) -> Optional[str]:
    """Extract patient name from raw document text."""
    match = re.search(r"Patient(?:\s+Name)?[:\s]+([A-Za-z][A-Za-z\s]{2,40})", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        for noise in ["Age", "Sex", "DOB", "Date", "Diagnosis", "Rx"]:
            if noise.lower() in name.lower():
                name = name[:name.lower().index(noise.lower())].strip()
        return name if len(name) > 2 else None
    return None


def _extract_hospital(text: str) -> Optional[str]:
    """Extract hospital or clinic name from raw document text."""
    match = re.search(
        r"([A-Za-z][A-Za-z\s]{2,50}(?:Clinic|Hospital|Healthcare|Care Centre|Medical Center|Pharmacy|Care))",
        text, re.IGNORECASE
    )
    return match.group(1).strip() if match else None


def _extract_treatment_date(text: str) -> Optional[str]:
    """Extract and normalize treatment/consultation date from document."""
    patterns = [
        r"Date[:\s]+(\d{4}-\d{2}-\d{2})",
        r"Date[:\s]+(\d{2}/\d{2}/\d{4})",
        r"Date[:\s]+(\d{2}-\d{2}-\d{4})",
        r"Date[:\s]+(\d{2}\.\d{2}\.\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1)
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]:
                try:
                    return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None


def _local_fallback(documents_text: str) -> Dict[str, Any]:
    """
    Local regex fallback when Gemini API is unavailable.
    Returns a well-structured extraction dict compatible with the adjudicator.
    """
    p_data = parse_prescription_regex(documents_text)
    b_data = parse_bill_regex(documents_text)
    claim_sum = sum(val for val in b_data.values() if isinstance(val, (int, float)))
    return {
        "document_types": ["prescription", "invoice"],
        "patient_name": _extract_patient_name(documents_text),
        "patient_age": None,
        "patient_gender": None,
        "doctor_name": p_data.get("doctor_name"),
        "doctor_registration_number": p_data.get("doctor_registration_number"),
        "hospital_or_clinic": _extract_hospital(documents_text),
        "treatment_date": _extract_treatment_date(documents_text),
        "consultation_date": _extract_treatment_date(documents_text),
        "invoice_numbers": [],
        "diagnosis": p_data.get("diagnosis"),
        "medicines": p_data.get("medicines"),
        "tests_prescribed": p_data.get("tests_prescribed"),
        "procedures": p_data.get("procedures"),
        "bill_breakdown": b_data,
        "claim_amount": claim_sum if claim_sum > 0 else None,
        "payment_mode": None,
        "documents_detected": ["Prescription", "Bill"],
        "missing_documents": [],
        "document_issues": [],
        "date_mismatches": [],
        "authenticity_flags": [],
        "possible_fraud_flags": [],
        "ocr_quality_issues": [],
        "ocr_confidence": 0.72,
        "extraction_confidence": 0.75,
    }


def run_extraction_pipeline(
    documents_text: str,
    image_bytes: Optional[bytes] = None,
    image_mime: str = "image/jpeg",
) -> Dict[str, Any]:
    """
    Orchestrates OCR parsing. Priority order:
      1. Gemini 2.5 Flash Vision (if image_bytes provided — real scanned document)
      2. Gemini 2.5 Flash text mode (if only text is provided)
      3. Local regex fallback (if API unavailable or key missing)

    Returns a structured extraction dict consumed by the adjudicator.
    """
    try:
        system_prompt = load_prompt_by_name("extraction_prompt.txt")

        if image_bytes:
            # Vision mode: pass raw binary image to Gemini Vision
            prompt_hint = (
                "Analyze this uploaded medical document image carefully. "
                "Extract all medical, billing, and patient information in structured JSON."
            )
            extractions = call_gemini_api(system_prompt, prompt_hint, image_bytes, image_mime)
        else:
            # Text mode: process pasted or extracted document text
            extractions = call_gemini_api(system_prompt, documents_text)

        return extractions

    except Exception as e:
        print(f"Gemini extraction API failed, running local regex parser fallback: {e}")
        return _local_fallback(documents_text)
