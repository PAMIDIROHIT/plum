# =====================================================================
# Clean Architecture - Coverage & Copay Rules Sub-engine
# =====================================================================

from typing import Dict, Any

def apply_coverage_concessions(
    category: str,
    claimed_amount: float,
    policy: Dict[str, Any],
    is_network: bool
) -> Dict[str, float]:
    """
    Applies co-payment percentages and network provider discounts based on policy terms.
    Returns calculated values.
    """
    copay_applied = 0.0
    network_discount_applied = 0.0
    after_discount = claimed_amount

    if category in ["consultation_fees", "consultation_fee"]:
        # Apply network hospital discount (typically 20%)
        if is_network:
            discount_pct = policy["coverage_details"]["consultation_fees"].get("network_discount", 20) / 100.0
            discount = claimed_amount * discount_pct
            network_discount_applied = discount
            after_discount -= discount

        # Apply co-payment percentage (typically 10%)
        copay_pct = policy["coverage_details"]["consultation_fees"].get("copay_percentage", 10) / 100.0
        copay = after_discount * copay_pct
        copay_applied = copay
        approved_amount = after_discount - copay
    else:
        approved_amount = claimed_amount

    return {
        "approved_amount": approved_amount,
        "copay_applied": copay_applied,
        "network_discount_applied": network_discount_applied
    }
