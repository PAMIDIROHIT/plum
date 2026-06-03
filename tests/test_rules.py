import json
import os
import sys

# Append backend directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.services.rule_engine import adjudicate_claim_local

def load_test_policy():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assignment_docs", "policy_terms.json")
    with open(path, "r") as f:
        return json.load(f)

def test_consultation_approved():
    policy = load_test_policy()
    claim = {
        "member_name": "Rajesh Kumar",
        "claim_amount": 1500.0,
        "hospital": "Apollo Clinic",
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Rahul Sharma",
                "doctor_reg": "KA/45678/2015",
                "diagnosis": "Viral fever"
            },
            "bill": {
                "consultation_fee": 1000,
                "diagnostic_tests": 500
            }
        }
    }
    
    result = adjudicate_claim_local(claim, policy)
    assert result["decision"] == "APPROVED"
    assert result["approved_amount"] == 1350.0

def test_diabetes_waiting_period():
    policy = load_test_policy()
    claim = {
        "member_name": "Vikram Joshi",
        "claim_amount": 3000.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Mehta",
                "doctor_reg": "GJ/56789/2014",
                "diagnosis": "Type 2 Diabetes"
            },
            "bill": {
                "consultation_fee": 1000,
                "medicines": 2000
            }
        }
    }
    
    result = adjudicate_claim_local(claim, policy)
    assert result["decision"] == "REJECTED"
    assert "WAITING_PERIOD" in result["rejection_reasons"]
