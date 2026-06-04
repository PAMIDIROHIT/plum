import base64
import requests
import json
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
invoice_path = "/Users/pamidirohit/.gemini/antigravity-ide/brain/233aa8a2-e060-47f0-a0c1-a733d8d16baa/test_apollo_invoice_1780550733430.png"
prescription_path = "/Users/pamidirohit/.gemini/antigravity-ide/brain/233aa8a2-e060-47f0-a0c1-a733d8d16baa/test_apollo_prescription_1780550755497.png"

documents = []

def add_doc(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            documents.append({
                "filename": os.path.basename(path),
                "content_type": "image/png",
                "base64_data": encoded
            })

add_doc(invoice_path)
add_doc(prescription_path)

if not documents:
    print("Documents not found, skipping E2E real image test.")
    exit(0)

payload = {
    "member_id": "EMP101",
    "treatment_date": "2026-06-04",
    "claim_amount": 1875.0,
    "documents": documents
}

print("Submitting to E2E Pipeline...")
try:
    resp = requests.post("http://localhost:8000/api/claims/submit", json=payload, timeout=60)
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
