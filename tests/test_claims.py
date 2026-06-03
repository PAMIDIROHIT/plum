import os
import sys
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Plum Adjudicate Backend"}

def test_claims_history_empty_ok():
    response = client.get("/api/claims/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
