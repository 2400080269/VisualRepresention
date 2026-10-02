"""
Tests for Machine Learning Predictions API (Phase 7).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    uid = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"pred_user_{uid}",
        "email": f"pred_{uid}@example.com",
        "password": "ValidPassword123!",
        "role": "USER"
    }
    client.post("/api/auth/register", json=user_data)
    login_res = client.post("/api/auth/login", json={
        "username_or_email": user_data["username"],
        "password": user_data["password"]
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_predict_success(client, auth_headers):
    payload = {
        "attendance_pct": 88.0,
        "internal": 18.0,
        "mid1": 22.0,
        "mid2": 23.0,
        "assignment": 9.0,
        "student_name": "Test Performer"
    }
    response = client.post("/api/predictions", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_category" in data
    assert 0 <= data["predicted_final_score"] <= 100
    assert 0 <= data["estimated_overall_percentage"] <= 100
    assert "category_probabilities" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0

def test_predict_at_risk_scenario(client, auth_headers):
    # Very low attendance and low internal
    payload = {
        "attendance_pct": 45.0,
        "internal": 8.0,
        "mid1": 10.0,
        "mid2": 9.0,
        "assignment": 4.0
    }
    response = client.post("/api/predictions", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_at_risk"] is True
    assert "High Risk" in data["risk_label"] or "At Risk" in data["risk_label"]

def test_predict_validation_out_of_bounds(client, auth_headers):
    # Invalid internal mark > 20
    payload = {
        "attendance_pct": 85.0,
        "internal": 28.0,  # Max is 20
        "mid1": 20.0,
        "mid2": 20.0,
        "assignment": 8.0
    }
    response = client.post("/api/predictions", json=payload, headers=auth_headers)
    assert response.status_code == 422

def test_get_prediction_history(client, auth_headers):
    response = client.get("/api/predictions", headers=auth_headers)
    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
    assert len(history) > 0
