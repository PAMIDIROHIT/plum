import re
from datetime import datetime
from typing import Dict, Any

def is_valid_doctor_reg(reg_num: str) -> bool:
    """
    Validates a doctor registration number against Indian medical council registration formats.
    
    Supported formats:
      - Standard:     XX/12345/2015  (2-letter state code / number / year)
      - Ayurvedic:    AYUR/KL/2345/2019  (4-segment council format)
      - Specialist:   MCI/12345/2018, DCI/23456/2016 etc.
    """
    if not reg_num:
        return False
        
    # 1. Normalize OCR spaces and backslashes
    normalized = re.sub(r'\s+', '', str(reg_num).upper())
    normalized = re.sub(r'\\\\', '/', normalized)
    
    # 2. Fix OCR slash errors where '/' is read as 'V'
    normalized = re.sub(r'^([A-Z]{2})[Vv](\d)', r'\1/\2', normalized)
    
    # 3. Add missing first slash if absent (e.g. KA12345/2015 -> KA/12345/2015)
    if re.match(r"^[A-Z]{2}\d", normalized):
        normalized = normalized[:2] + '/' + normalized[2:]
    
    # 4a. Standard format: XX/12345/2015 (per assignment spec)
    if re.match(r"^[A-Z]{2}/\d{4,6}/\d{4}$", normalized):
        return True
    
    # 4b. Specialist/Council 3-segment: MCI/12345/2018, DCI/23456/2016, AYUR/2345/2019
    if re.match(r"^[A-Z]{2,6}/\d{4,6}/\d{4}$", normalized):
        return True
    
    # 4c. Ayurvedic 4-segment: AYUR/KL/2345/2019, UNANI/MH/1234/2020
    if re.match(r"^[A-Z]{2,6}/[A-Z]{2}/\d{4,6}/\d{4}$", normalized):
        return True
    
    return False

def validate_eligibility_checks(claim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates patient metadata, doctor prescription existence, registration number,
    minimum claim thresholds, and submission timelines.
    """
    # 1. Check Minimum Claim Amount (e.g. ₹500)
    claim_amount = claim.get("claim_amount", 0)
    if claim_amount < 500:
        return {
            "eligible": False,
            "rejection_reason": "BELOW_MIN_AMOUNT",
            "notes": f"Claim amount ₹{claim_amount} is below the minimum threshold of ₹500.",
            "next_steps": "OPD claims must be for ₹500 or more to be eligible for reimbursement."
        }

    # 2. Check Late Submission (within 30 days of treatment)
    # We only enforce this if an explicit submission_date is provided in the claim.
    # If absent (e.g., test cases, demo runs), we skip — the real submission date is
    # captured at API ingestion time, not carried in the structured document payload.
    treatment_date_str = claim.get("treatment_date")
    submission_date_str = claim.get("submission_date")   # explicit override (optional)
    if treatment_date_str and submission_date_str:
        try:
            treatment_date = datetime.strptime(treatment_date_str, "%Y-%m-%d")
            submission_date = datetime.strptime(submission_date_str, "%Y-%m-%d")
            days_elapsed = (submission_date - treatment_date).days
            if days_elapsed > 30:
                return {
                    "eligible": False,
                    "rejection_reason": "LATE_SUBMISSION",
                    "notes": f"Claim submitted {days_elapsed} days after treatment. Maximum allowed timeline is 30 days.",
                    "next_steps": "OPD reimbursement claims must be submitted within 30 days of the treatment date."
                }
        except Exception:
            pass

    # 3. Check Prescription existence
    presc = claim.get("documents", {}).get("prescription")
    if not presc:
        return {
            "eligible": False,
            "rejection_reason": "MISSING_DOCUMENTS",
            "notes": "Prescription from registered doctor is required",
            "next_steps": "Please upload the doctor's prescription and resubmit."
        }

    # 4. Check Doctor Registration
    doctor_reg = presc.get("doctor_reg") or presc.get("doctor_registration_number", "")
    if not doctor_reg or not is_valid_doctor_reg(doctor_reg):
        return {
            "eligible": False,
            "rejection_reason": "DOCTOR_REG_INVALID",
            "notes": f"Doctor registration number '{doctor_reg}' is invalid or missing.",
            "next_steps": "Provide a valid prescription containing the doctor's official registration number."
        }
        
    return {"eligible": True, "rejection_reason": None}
