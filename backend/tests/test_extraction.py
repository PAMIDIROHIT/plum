import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.document_processing.document_classifier import parse_prescription_regex, parse_bill_regex

def test_parse_prescription_regex():
    prescription_text = """
    Dr. Rahul Sharma, MBBS MD
    Reg. No: KA/45678/2015
    Diagnosis: Viral fever
    """
    data = parse_prescription_regex(prescription_text)
    assert data["doctor_name"] == "Dr. Rahul Sharma"
    assert data["doctor_registration_number"] == "KA/45678/2015"
    assert data["diagnosis"] == "Viral fever"

def test_parse_bill_regex():
    bill_text = """
    Consultation Fee: ₹ 1000
    Medicines: ₹ 500
    """
    data = parse_bill_regex(bill_text)
    assert data["consultation_fee"] == 1000.0
    assert data["medicines"] == 500.0
