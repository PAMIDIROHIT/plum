# =====================================================================
# Fraud Detection - Claim Anomaly Detector
# =====================================================================

from typing import Dict, Any, List

def detect_claim_anomalies(claim: Dict[str, Any]) -> List[str]:
    """
    Examines transaction value spreads to flag unusual anomalies (e.g. excessive costs).
    """
    flags = []
    claim_amount = claim.get("claim_amount", 0.0)
    if claim_amount > 25000:
        flags.append("High-value claim")
    return flags
