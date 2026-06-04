# =====================================================================
# Document Processing - OCR Quality Validator
# =====================================================================

import re
from typing import Dict, Any, List


def assess_document_quality(text: str) -> Dict[str, Any]:
    """
    Analyses raw extracted text for OCR quality indicators:
    - Presence of required medical fields
    - Text readability and length
    - Formatting artifacts from poor scans

    Returns a quality assessment dict with an overall quality score [0–1].
    """
    issues: List[str] = []
    score = 1.0

    if not text or not text.strip():
        return {
            "quality_score": 0.0,
            "issues": ["Document is blank or completely unreadable."],
            "is_legible": False,
            "missing_fields": ["All fields"],
        }

    words = text.split()
    total_words = len(words)
    total_chars = len(text)

    # 1. Minimum content check
    if total_words < 10:
        issues.append("Document too short — likely partially scanned or truncated.")
        score -= 0.4
    elif total_words < 25:
        issues.append("Document content is sparse — may be incomplete.")
        score -= 0.15

    # 2. Garbled character detection (high ratio of non-alphanumeric chars)
    printable_ratio = sum(c.isalnum() or c.isspace() for c in text) / max(total_chars, 1)
    if printable_ratio < 0.6:
        issues.append("High proportion of special characters — possible garbled OCR output.")
        score -= 0.25
    elif printable_ratio < 0.75:
        issues.append("Moderate OCR noise detected.")
        score -= 0.10

    # 3. Repeated character artifact detection (e.g., "AAAA", "----")
    if re.search(r"(.)\1{5,}", text):
        issues.append("Repeated character artifacts detected — possible scan artefacts.")
        score -= 0.08

    # 4. Medical field presence checks
    missing_fields = []
    field_checks = {
        "Patient name": re.search(r"patient|name", text, re.IGNORECASE),
        "Doctor name": re.search(r"dr\.|doctor|vaidya", text, re.IGNORECASE),
        "Date": re.search(r"\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2}", text),
        "Amount": re.search(r"₹\s*\d+|\brs\.?\s*\d+|\btotal\b", text, re.IGNORECASE),
    }

    for field_name, match in field_checks.items():
        if not match:
            missing_fields.append(field_name)
            score -= 0.05

    # 5. Doctor registration format check
    reg_match = re.search(r"[A-Z]{2,6}/\d{4,6}/\d{4}", text, re.IGNORECASE)
    if not reg_match:
        missing_fields.append("Doctor registration number")
        score -= 0.08

    return {
        "quality_score": round(max(0.0, min(1.0, score)), 4),
        "issues": issues,
        "is_legible": score >= 0.5,
        "missing_fields": missing_fields,
        "word_count": total_words,
        "char_count": total_chars,
        "printable_ratio": round(printable_ratio, 3),
    }


def validate_document_pair(prescription_text: str, bill_text: str) -> Dict[str, Any]:
    """
    Cross-validates prescription and bill for date consistency and patient name consistency.
    """
    results = {
        "date_consistent": True,
        "patient_consistent": True,
        "issues": [],
    }

    # Extract all dates from both documents
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4}")
    presc_dates = set(date_pattern.findall(prescription_text))
    bill_dates = set(date_pattern.findall(bill_text))

    # Check for date overlap between prescription and bill
    if presc_dates and bill_dates and not presc_dates.intersection(bill_dates):
        results["date_consistent"] = False
        results["issues"].append(
            f"Date mismatch: prescription dates {presc_dates} do not match bill dates {bill_dates}."
        )

    # Check patient name consistency
    name_pattern = re.compile(r"patient(?:\s+name)?[:\s]+([A-Za-z][\w\s]{2,40})", re.IGNORECASE)
    presc_names = name_pattern.findall(prescription_text)
    bill_names = name_pattern.findall(bill_text)

    if presc_names and bill_names:
        presc_name = presc_names[0].strip().lower()
        bill_name = bill_names[0].strip().lower()
        # Allow minor prefix/suffix differences
        if not (presc_name in bill_name or bill_name in presc_name):
            results["patient_consistent"] = False
            results["issues"].append(
                f"Patient name mismatch: prescription '{presc_names[0]}' vs bill '{bill_names[0]}'."
            )

    return results
