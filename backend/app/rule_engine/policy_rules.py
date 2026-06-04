from datetime import datetime, timedelta
from typing import Dict, Any

def check_policy_waiting_periods(
    claim: Dict[str, Any],
    policy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validates waiting period regulations (initial period or specific diseases like diabetes).
    """
    diagnosis = (claim.get("documents", {}).get("prescription", {}).get("diagnosis") or "").lower()
    
    join_date_str = claim.get("member_join_date")
    treatment_date_str = claim.get("treatment_date")
    
    # If dates are not provided, skip waiting period check (assumption: waiting period already satisfied)
    if not join_date_str or not treatment_date_str:
        return {"eligible": True, "rejection_reason": None}

    try:
        join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
        treatment_date = datetime.strptime(treatment_date_str, "%Y-%m-%d")
        days_since_joining = (treatment_date - join_date).days
        
        # 0. Check if treatment date is BEFORE policy start date (Negative days)
        if days_since_joining < 0:
            return {
                "eligible": False,
                "rejection_reason": "POLICY_INACTIVE",
                "notes": f"Treatment date ({treatment_date_str}) is before the policy start date ({join_date_str}).",
                "next_steps": "Cannot claim for treatments that occurred before policy inception."
            }
            
        # 1. Check initial waiting period (usually 30 days)
        initial_waiting = policy.get("waiting_periods", {}).get("initial_waiting", 30)
        if days_since_joining < initial_waiting:
            eligible_date = join_date + timedelta(days=initial_waiting)
            eligible_date_str = eligible_date.strftime("%Y-%m-%d")
            return {
                "eligible": False,
                "rejection_reason": "WAITING_PERIOD",
                "notes": f"Treatment falls within the initial waiting period of {initial_waiting} days (joined: {join_date_str}, treatment: {treatment_date_str}).",
                "next_steps": f"Resubmit claims for treatments after initial waiting period expires (eligible from {eligible_date_str})."
            }
        
        # 2. Check specific pre-existing ailment waiting checks
        specific_ailments = policy.get("waiting_periods", {}).get("specific_ailments", {})
        for ailment, waiting_days in specific_ailments.items():
            if ailment.lower() in diagnosis:
                if days_since_joining < waiting_days:
                    eligible_date = join_date + timedelta(days=waiting_days)
                    eligible_date_str = eligible_date.strftime("%Y-%m-%d")
                    return {
                        "eligible": False,
                        "rejection_reason": "WAITING_PERIOD",
                        "notes": f"{ailment.capitalize()} has {waiting_days}-day waiting period. Eligible from {eligible_date_str}",
                        "next_steps": f"Resubmit the claim after the waiting period expires on {eligible_date_str}."
                    }
    except Exception as e:
        pass
        
    return {"eligible": True, "rejection_reason": None}
