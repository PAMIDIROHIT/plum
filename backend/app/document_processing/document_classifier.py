# =====================================================================
# Document Processing - Document Classification and Regex Extractions
# =====================================================================

import re
from typing import Dict, Any

def classify_document(text: str) -> str:
    """
    Classifies a raw text string into a category (prescription, bill, or other).
    """
    cleaned = text.lower()
    if "rx:" in cleaned or "prescription" in cleaned or "diagnosis:" in cleaned:
        return "prescription"
    if "invoice" in cleaned or "bill" in cleaned or "total" in cleaned:
        return "invoice"
    return "unknown"

def parse_prescription_regex(text: str) -> Dict[str, Any]:
    """
    Regex fallback prescription document text parser.
    Extracts doctor details, registration numbers, and clinical diagnoses.
    """
    data = {
        "doctor_name": "Unknown Doctor",
        "doctor_registration_number": "",
        "diagnosis": "Not specified",
        "medicines": [],
        "procedures": [],
        "tests_prescribed": []
    }
    
    # Extract Doctor Name
    doc_name_match = re.search(r"Dr\.\s*([A-Za-z\s]+)", text)
    if doc_name_match:
        data["doctor_name"] = f"Dr. {doc_name_match.group(1).strip()}"
        
    # Extract Registration Number (Format: KA/45678/2015, MH/23456/2018 etc.)
    reg_match = re.search(r"(?:Reg\.?\s*No:?\s*)?([A-Z]{2,4}\/\d{4,6}\/\d{4})", text, re.IGNORECASE)
    if reg_match:
        data["doctor_registration_number"] = reg_match.group(1)
    else:
        # Direct capture check
        direct_match = re.search(r"([A-Z]{2,4}\/\d{4,6}\/\d{4})", text)
        if direct_match:
            data["doctor_registration_number"] = direct_match.group(1)
            
    # Extract Diagnosis
    diag_match = re.search(r"Diagnosis:\s*\n?([^\n\r]+)", text, re.IGNORECASE)
    if diag_match:
        data["diagnosis"] = diag_match.group(1).strip()
        
    # Check for procedures
    if "root canal" in text.lower():
        data["procedures"].append("Root canal treatment")
    if "whitening" in text.lower():
        data["procedures"].append("Teeth whitening")
    if "panchakarma" in text.lower():
        data["procedures"].append("Panchakarma therapy")
        
    # Check for test details
    if "cbc" in text.lower():
        data["tests_prescribed"].append("CBC")
    if "dengue" in text.lower():
        data["tests_prescribed"].append("Dengue test")
    if "mri" in text.lower():
        data["tests_prescribed"].append("MRI scan")

    return data

def parse_bill_regex(text: str) -> Dict[str, float]:
    """
    Regex fallback billing invoice parser.
    Extracts consultation fees, medicines, procedures, and test amounts.
    """
    data = {}
    
    # Matching terms and numeric values (supporting optional colons and spaces)
    patterns = {
        "consultation_fee": r"Consultation\s*Fee[s]?\s*:?\s*₹?\s*(\d+)",
        "medicines": r"Medicines?\s*:?\s*₹?\s*(\d+)",
        "root_canal": r"Root\s*Canal\s*(?:treatment)?\s*:?\s*₹?\s*(\d+)",
        "teeth_whitening": r"Teeth\s*Whitening\s*:?\s*₹?\s*(\d+)",
        "diagnostic_tests": r"Diagnostic\s*Tests?:?\s*:?\s*₹?\s*(\d+)",
        "mri_scan": r"MRI\s*(?:Scan|Spine)?\s*:?\s*₹?\s*(\d+)",
        "therapy_charges": r"Therapy\s*(?:Charges)?\s*:?\s*₹?\s*(\d+)",
        "diet_plan": r"Diet\s*Plan\s*:?\s*₹?\s*(\d+)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = float(match.group(1))
            
    return data
