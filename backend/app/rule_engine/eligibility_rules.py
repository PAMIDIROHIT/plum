# =====================================================================
# Clean Architecture - Eligibility Rules Sub-engine
# =====================================================================

import re
from typing import Dict, Any

def is_valid_doctor_reg(reg_num: str) -> bool:
    """
    Validates a doctor registration number against the standard Indian medical registration format.
    Format expected: [State Code or Dept]/[Registration Number]/[Year]
    """
    if not reg_num:
        return False
    segments = reg_num.split('/')
    if len(segments) < 3:
        return False
    # Check if first segment starts with state/dept code characters
    return bool(re.match(r"^[A-Z]+", segments[0], re.IGNORECASE))

def validate_eligibility_checks(claim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates patient metadata, doctor prescription existence, and registration number.
    Returns evaluation dict with success status and keys.
    """
    presc = claim.get("documents", {}).get("prescription")
    if not presc:
        return {
            "eligible": False,
            "rejection_reason": "MISSING_DOCUMENTS",
            "notes": "Prescription from registered doctor is required",
            "next_steps": "Please upload the doctor's prescription and resubmit."
        }

    doctor_reg = presc.get("doctor_reg") or presc.get("doctor_registration_number", "")
    if not doctor_reg or not is_valid_doctor_reg(doctor_reg):
        return {
            "eligible": False,
            "rejection_reason": "DOCTOR_REG_INVALID",
            "notes": f"Doctor registration number '{doctor_reg}' is invalid or missing.",
            "next_steps": "Provide a valid prescription containing the doctor's official registration number."
        }
        
    return {"eligible": True, "rejection_reason": None}
