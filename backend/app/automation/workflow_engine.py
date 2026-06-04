# =====================================================================
# Automation - Claims State Machine Workflow Engine
# =====================================================================

from datetime import datetime
from typing import Dict, Any

# Allowed state transitions
VALID_TRANSITIONS = {
    "SUBMITTED":       ["PROCESSING"],
    "PROCESSING":      ["APPROVED", "REJECTED", "PARTIAL", "MANUAL_REVIEW"],
    "APPROVED":        ["SETTLED"],
    "PARTIAL":         ["SETTLED"],
    "REJECTED":        ["APPEALED"],
    "MANUAL_REVIEW":   ["APPROVED", "REJECTED"],
    "APPEALED":        ["MANUAL_REVIEW"],
    "SETTLED":         [],  # Terminal state
}

# Human-readable descriptions per state
STATE_DESCRIPTIONS = {
    "SUBMITTED":     "Claim received and queued for processing.",
    "PROCESSING":    "Claim is being evaluated against policy rules and AI pipeline.",
    "APPROVED":      "Claim approved. Reimbursement will be credited to registered account.",
    "PARTIAL":       "Claim partially approved. Some items were excluded from coverage.",
    "REJECTED":      "Claim rejected. See rejection reasons for details.",
    "MANUAL_REVIEW": "Claim flagged for human supervisor verification.",
    "APPEALED":      "Claim appealed. Awaiting re-evaluation by senior reviewer.",
    "SETTLED":       "Claim fully settled and closed.",
}


def get_workflow_state(decision: str) -> str:
    """
    Maps an adjudication decision to the initial workflow state.
    """
    mapping = {
        "APPROVED":      "APPROVED",
        "PARTIAL":       "PARTIAL",
        "REJECTED":      "REJECTED",
        "MANUAL_REVIEW": "MANUAL_REVIEW",
    }
    return mapping.get(decision, "MANUAL_REVIEW")


def can_transition(from_state: str, to_state: str) -> bool:
    """Returns True if the given state transition is valid."""
    return to_state in VALID_TRANSITIONS.get(from_state, [])


def execute_claim_workflow(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derives the initial workflow state from adjudication decision and builds
    a rich lifecycle context object with timestamp and next-action recommendations.
    """
    decision = claim_data.get("decision", "MANUAL_REVIEW")
    current_state = get_workflow_state(decision)
    next_states = VALID_TRANSITIONS.get(current_state, [])

    return {
        "workflow_state": current_state,
        "state_description": STATE_DESCRIPTIONS.get(current_state, ""),
        "allowed_next_states": next_states,
        "entered_at": datetime.utcnow().isoformat(),
        "is_terminal": current_state == "SETTLED",
        "requires_human_action": current_state in ("MANUAL_REVIEW", "APPEALED"),
    }


def transition_workflow(current_state: str, to_state: str, actor: str = "system") -> Dict[str, Any]:
    """
    Validates and applies a state transition. Returns new workflow context.
    Raises ValueError if the transition is not allowed.
    """
    if not can_transition(current_state, to_state):
        raise ValueError(
            f"Invalid state transition: {current_state} → {to_state}. "
            f"Allowed: {VALID_TRANSITIONS.get(current_state, [])}"
        )

    return {
        "previous_state": current_state,
        "workflow_state": to_state,
        "state_description": STATE_DESCRIPTIONS.get(to_state, ""),
        "allowed_next_states": VALID_TRANSITIONS.get(to_state, []),
        "transitioned_at": datetime.utcnow().isoformat(),
        "actor": actor,
        "is_terminal": to_state == "SETTLED",
        "requires_human_action": to_state in ("MANUAL_REVIEW", "APPEALED"),
    }
