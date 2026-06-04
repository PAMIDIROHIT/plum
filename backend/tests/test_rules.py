"""
Comprehensive test suite for the Plum OPD Adjudication Rule Engine.
Covers all 10 reference test cases + 3 additional edge cases.
Uses dynamic dates (relative to today) to avoid LATE_SUBMISSION false rejections.
"""
import json
import os
import sys
from datetime import datetime, timedelta

# Ensure backend module is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.adjudication.claim_adjudicator import run_local_adjudication_flow


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_policy():
    """Load policy_terms.json from the assignment_docs directory."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "assignment_docs", "policy_terms.json")
    with open(path, "r") as f:
        return json.load(f)


def recent(days_ago: int = 5) -> str:
    """Date N days ago — stays within the 30-day submission window."""
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def join_date(days_ago: int = 200) -> str:
    """Member join date N days ago (default: well past all waiting periods)."""
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────────────
# TC001 — Viral fever consultation → APPROVED ₹1,350 (10% copay on ₹1,500)
# ─────────────────────────────────────────────────────────────────────────────
def test_tc001_consultation_approved():
    policy = load_policy()
    claim = {
        "member_name": "Rajesh Kumar",
        "member_id": "EMP001",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 1500.0,
        "hospital": "Apollo Clinic",
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Rahul Sharma",
                "doctor_reg": "KA/45678/2015",
                "diagnosis": "Viral fever",
            },
            "bill": {"consultation_fee": 1000, "diagnostic_tests": 500},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "APPROVED", f"TC001: {result}"
    assert abs(result["approved_amount"] - 1350.0) < 1.0, f"TC001 amount: {result['approved_amount']}"


# ─────────────────────────────────────────────────────────────────────────────
# TC002 — Dental: root canal ✅ + teeth whitening ❌ → PARTIAL ₹8,000
# ─────────────────────────────────────────────────────────────────────────────
def test_tc002_dental_partial():
    policy = load_policy()
    claim = {
        "member_name": "Priya Singh",
        "member_id": "EMP002",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 12000.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Patel",
                "doctor_reg": "MH/23456/2018",
                "diagnosis": "Tooth decay requiring root canal",
            },
            "bill": {"root_canal": 8000, "teeth_whitening": 4000},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "PARTIAL", f"TC002: {result}"
    assert abs(result["approved_amount"] - 8000.0) < 1.0, f"TC002 amount: {result['approved_amount']}"


# ─────────────────────────────────────────────────────────────────────────────
# TC003 — Per-claim limit exceeded → REJECTED: PER_CLAIM_EXCEEDED
# ─────────────────────────────────────────────────────────────────────────────
def test_tc003_per_claim_limit_exceeded():
    policy = load_policy()
    claim = {
        "member_name": "Amit Verma",
        "member_id": "EMP003",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 7500.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Gupta",
                "doctor_reg": "DL/34567/2016",
                "diagnosis": "Gastroenteritis",
            },
            "bill": {"consultation_fee": 2000, "medicines": 5500},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "REJECTED", f"TC003: {result}"
    assert "PER_CLAIM_EXCEEDED" in result["rejection_reasons"]


# ─────────────────────────────────────────────────────────────────────────────
# TC004 — Missing prescription → REJECTED: MISSING_DOCUMENTS
# ─────────────────────────────────────────────────────────────────────────────
def test_tc004_missing_prescription():
    policy = load_policy()
    claim = {
        "member_name": "Sneha Reddy",
        "member_id": "EMP004",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 2000.0,
        "documents": {
            "bill": {"consultation_fee": 1500, "medicines": 500},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "REJECTED", f"TC004: {result}"
    assert "MISSING_DOCUMENTS" in result["rejection_reasons"]


# ─────────────────────────────────────────────────────────────────────────────
# TC005 — Diabetes within 90-day waiting period → REJECTED: WAITING_PERIOD
# Member joined 45 days ago: past 30-day initial wait but inside 90-day diabetes wait
# ─────────────────────────────────────────────────────────────────────────────
def test_tc005_diabetes_waiting_period():
    policy = load_policy()
    claim = {
        "member_name": "Vikram Joshi",
        "member_id": "EMP005",
        "member_join_date": join_date(45),
        "treatment_date": recent(5),
        "claim_amount": 3000.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Mehta",
                "doctor_reg": "GJ/56789/2014",
                "diagnosis": "Type 2 Diabetes",
            },
            "bill": {"consultation_fee": 1000, "medicines": 2000},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "REJECTED", f"TC005: {result}"
    assert "WAITING_PERIOD" in result["rejection_reasons"]


# ─────────────────────────────────────────────────────────────────────────────
# TC006 — Alternative medicine (Ayurveda) within limits → APPROVED ₹4,000
# ─────────────────────────────────────────────────────────────────────────────
def test_tc006_alternative_medicine_approved():
    policy = load_policy()
    claim = {
        "member_name": "Kavita Nair",
        "member_id": "EMP006",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 4000.0,
        "documents": {
            "prescription": {
                "doctor_name": "Vaidya Krishnan",
                "doctor_reg": "AYUR/KL/2345/2019",
                "diagnosis": "Chronic joint pain",
            },
            "bill": {"consultation_fee": 1000, "therapy_charges": 3000},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "APPROVED", f"TC006: {result}"
    assert abs(result["approved_amount"] - 4000.0) < 1.0, f"TC006 amount: {result['approved_amount']}"


# ─────────────────────────────────────────────────────────────────────────────
# TC007 — MRI without pre-authorization → REJECTED: PRE_AUTH_MISSING
# ─────────────────────────────────────────────────────────────────────────────
def test_tc007_mri_preauth_missing():
    policy = load_policy()
    claim = {
        "member_name": "Suresh Patil",
        "member_id": "EMP007",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 15000.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Rao",
                "doctor_reg": "AP/67890/2017",
                "diagnosis": "Suspected lumbar disc herniation",
            },
            "bill": {"mri_scan": 15000},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "REJECTED", f"TC007: {result}"
    assert "PRE_AUTH_MISSING" in result["rejection_reasons"]


# ─────────────────────────────────────────────────────────────────────────────
# TC008 — 3+ claims same day (fraud signal) → MANUAL_REVIEW
# ─────────────────────────────────────────────────────────────────────────────
def test_tc008_fraud_manual_review():
    policy = load_policy()
    claim = {
        "member_name": "Ravi Menon",
        "member_id": "EMP008",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 4800.0,
        "previous_claims_same_day": 3,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Khan",
                "doctor_reg": "UP/45678/2016",
                "diagnosis": "Migraine",
            },
            "bill": {"consultation_fee": 2000, "medicines": 2800},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "MANUAL_REVIEW", f"TC008: {result}"


# ─────────────────────────────────────────────────────────────────────────────
# TC009 — Obesity/bariatric treatment excluded → REJECTED: SERVICE_NOT_COVERED
# ─────────────────────────────────────────────────────────────────────────────
def test_tc009_excluded_treatment():
    policy = load_policy()
    claim = {
        "member_name": "Anita Desai",
        "member_id": "EMP009",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 8000.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Banerjee",
                "doctor_reg": "WB/34567/2015",
                "diagnosis": "Obesity - BMI 35",
            },
            "bill": {"consultation_fee": 3000, "diet_plan": 5000},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "REJECTED", f"TC009: {result}"
    assert "SERVICE_NOT_COVERED" in result["rejection_reasons"]


# ─────────────────────────────────────────────────────────────────────────────
# TC010 — Apollo Hospitals cashless → APPROVED ₹3,600 (20% network discount)
# Calculation: (1500 + 3000) * 0.8 = 3600 (network discount applied, no copay for cashless)
# ─────────────────────────────────────────────────────────────────────────────
def test_tc010_network_cashless():
    policy = load_policy()
    claim = {
        "member_name": "Deepak Shah",
        "member_id": "EMP010",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 4500.0,
        "hospital": "Apollo Hospitals",
        "cashless_request": True,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Iyer",
                "doctor_reg": "TN/56789/2013",
                "diagnosis": "Acute bronchitis",
            },
            "bill": {"consultation_fee": 1500, "medicines": 3000},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "APPROVED", f"TC010: {result}"
    assert abs(result["approved_amount"] - 3600.0) < 1.0, f"TC010 amount: {result['approved_amount']}"


# ─────────────────────────────────────────────────────────────────────────────
# Extra — Below minimum claim amount → REJECTED: BELOW_MIN_AMOUNT
# ─────────────────────────────────────────────────────────────────────────────
def test_below_minimum_amount():
    policy = load_policy()
    claim = {
        "member_name": "Test User",
        "member_id": "EMP099",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 200.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Test",
                "doctor_reg": "KA/12345/2020",
                "diagnosis": "Common cold",
            },
            "bill": {"consultation_fee": 200},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "REJECTED"
    assert "BELOW_MIN_AMOUNT" in result["rejection_reasons"]


# ─────────────────────────────────────────────────────────────────────────────
# Extra — Initial 30-day waiting period → REJECTED: WAITING_PERIOD
# ─────────────────────────────────────────────────────────────────────────────
def test_initial_waiting_period():
    policy = load_policy()
    claim = {
        "member_name": "New Member",
        "member_id": "EMP100",
        "member_join_date": join_date(10),   # Only 10 days since joining
        "treatment_date": recent(5),
        "claim_amount": 1500.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. New",
                "doctor_reg": "MH/99999/2020",
                "diagnosis": "Fever",
            },
            "bill": {"consultation_fee": 1500},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "REJECTED"
    assert "WAITING_PERIOD" in result["rejection_reasons"]


# ─────────────────────────────────────────────────────────────────────────────
# Extra — Invalid doctor registration format → REJECTED: DOCTOR_REG_INVALID
# ─────────────────────────────────────────────────────────────────────────────
def test_invalid_doctor_registration():
    policy = load_policy()
    claim = {
        "member_name": "Test Patient",
        "member_id": "EMP101",
        "member_join_date": join_date(200),
        "treatment_date": recent(5),
        "claim_amount": 1200.0,
        "documents": {
            "prescription": {
                "doctor_name": "Dr. Fake",
                "doctor_reg": "INVALID123",  # Must be State/Number/Year format
                "diagnosis": "Back pain",
            },
            "bill": {"consultation_fee": 1200},
        },
    }
    result = run_local_adjudication_flow(claim, policy)
    assert result["decision"] == "REJECTED"
    assert "DOCTOR_REG_INVALID" in result["rejection_reasons"]
