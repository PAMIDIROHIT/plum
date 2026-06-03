# =====================================================================
# Adjudication - AI Confidence Scorer
# =====================================================================

def calculate_adjudication_confidence(meta: dict) -> float:
    """
    Calculates decision engine confidence based on document metadata metrics.
    """
    return float(meta.get("confidence_score", 0.95))
