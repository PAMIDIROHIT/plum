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

    # Helper: reject obviously wrong doctor names extracted from label text
    _BAD_DOC_NAMES = {'name', 'doctor', 'reg', 'no', 'number', 'mbbs', 'md', 'unknown'}

    def _is_valid_doctor_name(n: str) -> bool:
        words = n.lower().split()
        return len(words) >= 1 and not any(w in _BAD_DOC_NAMES for w in words) and len(n) > 2

    # Priority 1: Labeled field with Dr. prefix — "Doctor: Dr. Smith"
    doc_label_match = re.search(
        r"Doctor[:\s]+Dr\.?\s*([A-Za-z][A-Za-z ]{1,25}?)(?:\s*[\(\|,\n]|\s*MBBS|\s*MD|\s*$)",
        text, re.IGNORECASE
    )
    if doc_label_match:
        candidate = doc_label_match.group(1).strip()
        if _is_valid_doctor_name(candidate):
            data["doctor_name"] = f"Dr. {candidate}"

    if data["doctor_name"] == "Unknown Doctor":
        # Priority 2: Labeled field without Dr. prefix — "Doctor: Smith" or "Doctor Name: Iyer"
        doc_name_only = re.search(
            r"Doctor(?:\s+Name)?[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\s*[\(\|,\n]|\s*MBBS|\s*$)",
            text, re.IGNORECASE
        )
        if doc_name_only:
            candidate = doc_name_only.group(1).strip()
            if _is_valid_doctor_name(candidate):
                data["doctor_name"] = f"Dr. {candidate}"

    if data["doctor_name"] == "Unknown Doctor":
        # Priority 3: "Dr. Iyer" or "Dr Iyer" anywhere — stop BEFORE state code (2 caps + /)
        # Negative lookahead ensures we don't grab state code letters like 'TN' after the name
        dr_match = re.search(
            r"\bDr\.?\s+([A-Za-z][a-z]+(?:\s+(?!(?:[A-Z]{2}[/\s]|MBBS|MD|Name))[A-Z][a-z]+)?)",
            text, re.IGNORECASE
        )
        if dr_match:
            name_raw = dr_match.group(1).strip().title()
            # Remove any trailing noise (single uppercase letters that are state codes)
            name_raw = re.sub(r'\s+[A-Z][a-z]?$', '', name_raw).strip()
            if _is_valid_doctor_name(name_raw):
                data["doctor_name"] = f"Dr. {name_raw}"

    if data["doctor_name"] == "Unknown Doctor":
        # Priority 4: Consulting Doctor label from invoice
        consulting_match = re.search(
            r"Consulting\s+Doctor[:\s]+(?:DR\.?\s*)?([A-Za-z][A-Za-z ]{1,25}?)(?:\s*[\(\n,]|$)",
            text, re.IGNORECASE
        )
        if consulting_match:
            candidate = consulting_match.group(1).strip().title()
            if _is_valid_doctor_name(candidate):
                data["doctor_name"] = f"Dr. {candidate}"


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
    # Match "Diagnosis:" label and grab rest of the line
    diag_match = re.search(r"Diagnosis\s*:\s*([^\n\r]{3,120})", text, re.IGNORECASE)
    if diag_match:
        raw_diag = diag_match.group(1).strip()
        # Strip trailing noise like "Prescribed Medicines", "Doctor", or OCR artifacts
        raw_diag = re.split(r'\s*(?:Prescribed|Rx:|Medicines|Doctor|$)', raw_diag, flags=re.IGNORECASE)[0]
        # Clean OCR artifacts: trailing underscores, dashes, special chars
        raw_diag = re.sub(r'[_\-]+$', '', raw_diag).strip()
        # Clean embedded OCR underscores used as separators (e.g. "Acute_bronchitis")
        raw_diag = raw_diag.replace('_', ' ').strip()
        data["diagnosis"] = raw_diag if len(raw_diag) > 2 else "Not specified"

    # ── Medicines ─────────────────────────────────────────────────────────────
    medicines = []
    # Priority 1: Match Tab/Cap/Inj/Syp prefixed drugs
    med_matches = re.findall(
        r'(?:Tab(?:let)?\.?|Cap(?:sule)?\.?|Inj\.?|Syp\.?|Syr\.?|Drops?\.?)[\s.]*([A-Za-z][A-Za-z ]+(?:\d+\s*mg)?)',
        text, re.IGNORECASE
    )
    for m in med_matches:
        name = m.strip().rstrip('_-.')
        if 3 < len(name) < 60:
            medicines.append(name)
    # Priority 2: Numbered list items like "1. Paracetamol 650mg" if no prefix found
    if not medicines:
        num_meds = re.findall(
            r'^\s*\d+\.\s+([A-Za-z][A-Za-z ]+(?:\d+\s*mg)?)\b',
            text, re.IGNORECASE | re.MULTILINE
        )
        for m in num_meds:
            name = m.strip().rstrip('_-.')
            if 3 < len(name) < 60:
                medicines.append(name)
    # Priority 3: "Medicines: Amoxicillin, Salbutamol" labeled comma-separated list
    if not medicines:
        med_label = re.search(r'Medicines?[:\s]+(.+?)(?=\n|$)', text, re.IGNORECASE)
        if med_label:
            raw_meds = med_label.group(1).strip()
            for part in re.split(r'[,;]', raw_meds):
                part = part.strip().rstrip('_.').strip()
                if 3 < len(part) < 50:
                    medicines.append(part)
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
