# =====================================================================
# AI Pipeline - Fraud Detection Pipeline Coordinator
# =====================================================================

from typing import Dict, Any, List
from ..fraud_detection.fraud_checker import run_all_fraud_checks

def execute_fraud_pipeline(claim: Dict[str, Any]) -> List[str]:
    """
    Coordinates automated fraud analysis over raw claims inputs.
    """
    return run_all_fraud_checks(claim)
