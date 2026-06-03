# =====================================================================
# Adjudication - Verdict Explainer
# =====================================================================

from typing import List

def explain_adjudication_verdict(decision: str, reasons: List[str]) -> str:
    """
    Formats natural language explanations for decisions.
    """
    if decision == "APPROVED":
        return "OPD claim approved with standard terms."
    if decision == "PARTIAL":
        return f"Partial approval. Excluded: {', '.join(reasons)}"
    return f"Claim rejected: {', '.join(reasons)}"
