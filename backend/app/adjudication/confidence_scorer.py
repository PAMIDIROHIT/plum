# =====================================================================
# Adjudication - Multi-Factor AI Confidence Scorer
# =====================================================================

from typing import Dict, Any


def calculate_adjudication_confidence(
    meta: Dict[str, Any],
    extraction_data: Dict[str, Any] = None,
    claim: Dict[str, Any] = None
) -> float:
    """
    Calculates decision engine confidence from multiple quality signals:
    - Document extraction quality (OCR confidence)
    - Rule certainty (hard rule vs edge case)
    - Fraud indicators
    - Document completeness
    - Decision type (REJECTED hard rules are high confidence)

    Returns a float in [0.0, 1.0].
    """
    score = 1.0

    # --- 1. Extraction/OCR quality signal ---
    if extraction_data:
        ocr_conf = extraction_data.get("ocr_confidence", 0.85)
        ext_conf = extraction_data.get("extraction_confidence", 0.85)
        ocr_factor = (ocr_conf + ext_conf) / 2.0
        # OCR quality contributes 25% of the score
        score *= (0.75 + 0.25 * ocr_factor)

        # Penalize for document issues found during extraction
        doc_issues = extraction_data.get("document_issues", [])
        quality_issues = extraction_data.get("ocr_quality_issues", [])
        fraud_flags = extraction_data.get("possible_fraud_flags", [])

        score -= len(doc_issues) * 0.03
        score -= len(quality_issues) * 0.04
        score -= len(fraud_flags) * 0.06

    # --- 2. Rule certainty signal ---
    decision = meta.get("decision", "MANUAL_REVIEW")
    rejection_reasons = meta.get("rejection_reasons", [])

    # Hard rule rejections are very high confidence
    HIGH_CERTAINTY_REASONS = {
        "ANNUAL_LIMIT_EXCEEDED",
        "BELOW_MIN_AMOUNT",
        "PER_CLAIM_EXCEEDED",
        "SERVICE_NOT_COVERED",
        "PRE_AUTH_MISSING",
        "WAITING_PERIOD",
        "LATE_SUBMISSION",
    }
    MEDIUM_CERTAINTY_REASONS = {
        "DOCTOR_REG_INVALID",
        "MISSING_DOCUMENTS",
        "WAITING_PERIOD",
    }

    if decision == "REJECTED":
        if any(r in HIGH_CERTAINTY_REASONS for r in rejection_reasons):
            score = max(score, 0.93)  # Hard rule = high certainty floor
        elif any(r in MEDIUM_CERTAINTY_REASONS for r in rejection_reasons):
            score = max(score, 0.85)
    elif decision == "MANUAL_REVIEW":
        # Manual review means uncertainty — cap at 0.75
        score = min(score, 0.75)
        flags = meta.get("flags", []) or meta.get("fraud_flags", [])
        score -= len(flags) * 0.04
    elif decision == "PARTIAL":
        score = min(score, 0.94)
    elif decision == "APPROVED":
        score = min(score, 0.97)

    # --- 3. Claim completeness signal (from claim payload) ---
    if claim:
        if not claim.get("documents", {}).get("prescription"):
            score -= 0.10
        if not claim.get("member_id"):
            score -= 0.05
        if not claim.get("treatment_date"):
            score -= 0.05
        doctor_reg = (
            claim.get("documents", {})
            .get("prescription", {})
            .get("doctor_reg", "")
        )
        if not doctor_reg:
            score -= 0.05

    # --- 4. If meta already has a confidence, blend with it ---
    existing = meta.get("confidence_score")
    if existing and 0 < existing <= 1:
        score = round(0.6 * score + 0.4 * existing, 4)

    return round(max(0.0, min(1.0, score)), 4)
