"""
Tests for Machine Learning Model Info and Metrics API (Phase 8).
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
        "username": f"model_user_{uid}",
        "email": f"model_{uid}@example.com",
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

def test_get_model_info(client, auth_headers):
    response = client.get("/api/model/info", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "classifier_algorithm" in data
    assert "regressor_algorithm" in data
    assert "feature_names" in data
    assert "target_classes" in data
    assert len(data["feature_names"]) == 5
    assert len(data["target_classes"]) == 5

def test_get_model_metrics(client, auth_headers):
    response = client.get("/api/model/metrics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "classifier_accuracy" in data
    assert "regressor_r2_score" in data
    assert "regressor_rmse" in data
    assert "feature_importances" in data
    assert isinstance(data["feature_importances"], dict)
    assert "attendance_pct" in data["feature_importances"]
