# =====================================================================
# Clean Architecture - Limits & Sub-limits Rules Sub-engine
# =====================================================================

from typing import Dict, Any

def check_category_sub_limits(
    category: str,
    claimed_amount: float,
    approved_amount: float,
    policy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validates claim line item amounts against the dynamic policy category sub-limits.
    Caps approved amounts if limits are exceeded.
    """
    sub_limit = 999999.0
    is_exceeded = False
    rejection_detail = ""
    
    # Map raw bill keys to policy terms sections
    category_mapping = {
        "consultation_fee": "consultation_fees",
        "medicines": "pharmacy",
        "root_canal": "dental",
        "teeth_whitening": "dental",
        "therapy_charges": "alternative_medicine",
        "mri_scan": "diagnostic_tests",
        "diagnostic_tests": "diagnostic_tests"
    }
    
    policy_section = category_mapping.get(category)
    if policy_section and policy_section in policy["coverage_details"]:
        sub_limit = policy["coverage_details"][policy_section].get("sub_limit", 999999.0)
        
    if approved_amount > sub_limit:
        approved_amount = sub_limit
        is_exceeded = True
        rejection_detail = f"{category.replace('_', ' ').capitalize()} portion exceeding sub-limit of ₹{sub_limit}"
        
    return {
        "approved_amount": approved_amount,
        "is_exceeded": is_exceeded,
        "rejection_detail": rejection_detail,
        "sub_limit": sub_limit
    }
