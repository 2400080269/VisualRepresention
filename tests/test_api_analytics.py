"""
Tests for Analytics API endpoints (Phase 6).
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
        "username": f"analytics_user_{uid}",
        "email": f"analytics_{uid}@example.com",
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

def test_analytics_overview(client, auth_headers):
    response = client.get("/api/analytics/overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] > 0
    assert 0 <= data["average_marks"] <= 100
    assert 0 <= data["average_attendance"] <= 100
    assert 0 <= data["pass_percentage"] <= 100
    assert data["at_risk_count"] >= 0

def test_analytics_attendance(client, auth_headers):
    response = client.get("/api/analytics/attendance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "average_attendance_pct" in data
    assert "correlation" in data
    assert "pearson_r" in data["correlation"]
    assert "interpretation" in data["correlation"]
    assert "attendance_tiers" in data
    assert isinstance(data["attendance_tiers"], list)

def test_analytics_performance(client, auth_headers):
    response = client.get("/api/analytics/performance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "grade_distribution" in data
    assert "department_benchmarks" in data
    assert len(data["grade_distribution"]) > 0
    assert len(data["department_benchmarks"]) > 0

def test_analytics_subjects(client, auth_headers):
    response = client.get("/api/analytics/subjects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "strongest_subject" in data
    assert "weakest_subject" in data
    assert "subjects" in data
    assert len(data["subjects"]) > 0
