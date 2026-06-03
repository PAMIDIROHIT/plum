# =====================================================================
# Fraud Detection - Duplicate Submission Checker
# =====================================================================

from typing import Dict, Any, List

def check_duplicate_submissions(claim: Dict[str, Any]) -> List[str]:
    """
    Validates claim metadata history and detects high-frequency claim submissions.
    """
    flags = []
    prev_claims = claim.get("previous_claims_same_day", 0)
    if prev_claims >= 3:
        flags.append("Multiple claims same day")
        flags.append("Unusual pattern detected")
    return flags
