# =====================================================================
# Fraud Detection - Unified Fraud Checker Pipeline
# =====================================================================

from typing import Dict, Any, List
from .duplicate_claim_checker import check_duplicate_submissions
from .anomaly_detector import detect_claim_anomalies

def run_all_fraud_checks(claim: Dict[str, Any]) -> List[str]:
    """
    Combines all available fraud sub-engines and returns audit flags.
    """
    flags = []
    flags.extend(check_duplicate_submissions(claim))
    flags.extend(detect_claim_anomalies(claim))
    return flags
