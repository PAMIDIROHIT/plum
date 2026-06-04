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
    
    Designed to handle real Apollo/hospital document layouts from EasyOCR/raw text.
    """
    data = {
        "doctor_name": "Unknown Doctor",
        "doctor_registration_number": "",
        "diagnosis": "Not specified",
        "medicines": [],
        "procedures": [],
        "tests_prescribed": []
    }

    # ── Doctor Name ────────────────────────────────────────────────────────────
    # Priority 1: "Doctor: Dr. Smith" or "Doctor: Smith" labeled field
    doc_label_match = re.search(
        r"Doctor[:\s]+Dr\.?\s*([A-Za-z][A-Za-z\s]{1,30}?)(?:\s*[\(\|,\n]|\s*MBBS|\s*MD|\s*$)",
        text, re.IGNORECASE
    )
    if doc_label_match:
        data["doctor_name"] = f"Dr. {doc_label_match.group(1).strip()}"
    else:
        # Priority 2: "Dr. Smith" anywhere in text — take first non-trivial match
        dr_match = re.search(r"\bDr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", text)
        if dr_match:
            data["doctor_name"] = f"Dr. {dr_match.group(1).strip()}"
        else:
            # Priority 3: Consulting Doctor label from invoice
            consulting_match = re.search(
                r"Consulting\s+Doctor[:\s]+(?:DR\.?\s*)?([A-Za-z][A-Za-z\s]{1,25}?)(?:\s*[\(\n,]|$)",
                text, re.IGNORECASE
            )
            if consulting_match:
                data["doctor_name"] = f"Dr. {consulting_match.group(1).strip().title()}"

    # ── Doctor Registration Number ─────────────────────────────────────────────
    # ONLY match when preceded by a registration label to avoid prescription numbers.
    # Labels: "Reg No", "Reg. No", "Doctor Reg No", "Registration No"
    reg_with_label = re.search(
        r"(?:Doctor\s+Reg(?:istration)?\.?\s*No\.?|Reg(?:istration)?\.?\s*No\.?)[:\s]*([A-Z]{2,6}[/\s\\Vv]{0,3}\d{4,6}[/\s]*\d{4})",
        text, re.IGNORECASE
    )
    if reg_with_label:
        raw_reg = reg_with_label.group(1).strip()
        # Normalize: remove spaces, fix OCR slash artifacts
        norm = re.sub(r'\s+', '', raw_reg.upper())
        norm = re.sub(r'[\\Vv](?=\d)', '/', norm)
        # Insert missing first slash for 2-letter state codes
        if re.match(r'^[A-Z]{2}\d', norm):
            norm = norm[:2] + '/' + norm[2:]
        data["doctor_registration_number"] = norm
    else:
        # Fallback: strict 3-segment format only (XX/NNNNN/YYYY) to avoid prescription numbers
        strict_match = re.search(r'\b([A-Z]{2})/(\d{4,6})/(\d{4})\b', text)
        if strict_match:
            data["doctor_registration_number"] = f"{strict_match.group(1)}/{strict_match.group(2)}/{strict_match.group(3)}"

    # ── Diagnosis ─────────────────────────────────────────────────────────────
    # Match "Diagnosis:" or "Diagnosis :" label and grab rest of the line
    diag_match = re.search(r"Diagnosis\s*:\s*([^\n\r]{3,120})", text, re.IGNORECASE)
    if diag_match:
        raw_diag = diag_match.group(1).strip()
        # Strip trailing noise like "Prescribed Medicines" or similar
        raw_diag = re.split(r'\s*(?:Prescribed|Rx:|Medicines|Doctor)', raw_diag, flags=re.IGNORECASE)[0]
        data["diagnosis"] = raw_diag.strip() or "Not specified"

    # ── Medicines ─────────────────────────────────────────────────────────────
    medicines = []
    # Match numbered list items: "1. Tab. Paracetamol 650mg" or "1. Amoxicillin 500mg"
    med_matches = re.findall(
        r'(?:Tab(?:let)?\.?|Cap(?:sule)?\.?|Inj\.?|Syp\.?|Syr\.?|Drops?\.?)[\s.]*([A-Za-z][A-Za-z\s]+(?:\d+\s*mg)?)',
        text, re.IGNORECASE
    )
    for m in med_matches:
        name = m.strip()
        if 3 < len(name) < 60:
            medicines.append(name)
    if medicines:
        data["medicines"] = medicines[:8]  # cap at 8

    # ── Procedures ────────────────────────────────────────────────────────────
    if "root canal" in text.lower():
        data["procedures"].append("Root canal treatment")
    if "whitening" in text.lower():
        data["procedures"].append("Teeth whitening")
    if "panchakarma" in text.lower():
        data["procedures"].append("Panchakarma therapy")

    # ── Tests ────────────────────────────────────────────────────────────────
    if re.search(r'\bcbc\b', text, re.IGNORECASE):
        data["tests_prescribed"].append("CBC")
    if re.search(r'\bdengue\b', text, re.IGNORECASE):
        data["tests_prescribed"].append("Dengue test")
    if re.search(r'\bmri\b', text, re.IGNORECASE):
        data["tests_prescribed"].append("MRI scan")

    return data


def parse_bill_regex(text: str) -> Dict[str, float]:
    """
    Regex fallback billing invoice parser.
    Extracts consultation fees, medicines, procedures, and test amounts.
    
    Also handles Apollo-style tabular invoices where amounts appear at end of line.
    """
    data = {}

    # Standard labeled patterns
    patterns = {
        # Negative lookahead (?!/\d) prevents matching numbers like 04 from dates (04/06/2026)
        "consultation_fee": r"Consultation\s*(?:Fee[s]?)?(?:\s*-\s*[A-Z\.\s]+)?\s*[:\|]?\s*(?:1\s+)?(?:₹|Rs\.?)?\s*(\d[\d,]+(?:\.\d{1,2})?)(?!/\d)",
        "medicines": r"(?:Medicines?|Pharmacy|Medicine\s*-\s*Outpatient)\s*(?::\s*|\|\s*|[\d\s]+)(?:₹|Rs\.?)?\s*(\d[\d,]+(?:\.\d{1,2})?)(?!/\d)",
        "root_canal": r"Root\s*Canal\s*(?:treatment)?\s*:?\s*(?:₹|Rs\.?)?\s*(\d[\d,]+(?:\.\d{1,2})?)",
        "teeth_whitening": r"Teeth\s*Whitening\s*:?\s*(?:₹|Rs\.?)?\s*(\d[\d,]+(?:\.\d{1,2})?)",
        "diagnostic_tests": r"Diagnostic\s*Tests?\s*(?:\([A-Z]+\))?\s*:?\s*(?:₹|Rs\.?)?\s*(\d[\d,]+(?:\.\d{1,2})?)",
        "mri_scan": r"MRI\s*(?:Lumbar\s*)?(?:Scan|Spine)?\s*:?\s*(?:₹|Rs\.?)?\s*(\d[\d,]+(?:\.\d{1,2})?)",
        "therapy_charges": r"Therapy\s*(?:Charges)?\s*:?\s*(?:₹|Rs\.?)?\s*(\d[\d,]+(?:\.\d{1,2})?)",
        "diet_plan": r"Diet\s*Plan\s*:?\s*(?:₹|Rs\.?)?\s*(\d[\d,]+(?:\.\d{1,2})?)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                data[key] = float(amount_str)
            except ValueError:
                pass

    # Apollo tabular format: "CONSULTATION FEE - DR. SMITH  04/06/2026  1  1000.00  1000.00"
    # Pick the last number on the line — require 3+ digit amounts to skip date digits
    if "consultation_fee" not in data:
        tab_consult = re.search(
            r"CONSULTATION\s*(?:FEE)?[^\n]*?\s(\d{3,}\.?\d{0,2})\s*$",
            text, re.IGNORECASE | re.MULTILINE
        )
        if tab_consult:
            try:
                data["consultation_fee"] = float(tab_consult.group(1).replace(',', ''))
            except ValueError:
                pass

    if "medicines" not in data:
        tab_med = re.search(
            r"(?:MEDICINES?\s*-?\s*OUTPATIENT|PHARMACY)[^\n]*?(\d[\d,]+\.?\d{0,2})\s*$",
            text, re.IGNORECASE | re.MULTILINE
        )
        if tab_med:
            try:
                data["medicines"] = float(tab_med.group(1).replace(',', ''))
            except ValueError:
                pass

    # "TOTAL AMOUNT  1875.00" or "NET PAYABLE  1875.00" — cross-check total
    total_match = re.search(
        r"(?:TOTAL\s*AMOUNT|NET\s*PAYABLE|TOTAL)\s*[:\|]?\s*(?:₹|Rs\.?)?\s*(\d[\d,]+\.?\d{0,2})",
        text, re.IGNORECASE
    )
    if total_match:
        try:
            data["_total_amount"] = float(total_match.group(1).replace(',', ''))
        except ValueError:
            pass

    return data
