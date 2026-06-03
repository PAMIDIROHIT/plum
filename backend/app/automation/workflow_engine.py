# =====================================================================
# Automation - Claims State Machine Workflow Engine
# =====================================================================

from typing import Dict, Any

def execute_claim_workflow(claim_data: Dict[str, Any]) -> str:
    """
    Coordinates state transitions for processing claims lifecycle.
    """
    decision = claim_data.get("decision", "MANUAL_REVIEW")
    if decision == "MANUAL_REVIEW":
        return "PENDING_REVIEW"
    return "SETTLED"
