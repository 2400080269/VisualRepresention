"""
Tests for Student listing, filtering, at-risk, and detail APIs (Phase 5).
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
        "username": f"stu_user_{uid}",
        "email": f"stu_user_{uid}@example.com",
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

def test_list_students_paginated(client, auth_headers):
    response = client.get("/api/students?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total_count" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) <= 10

def test_list_students_filter_department(client, auth_headers):
    response = client.get("/api/students?department=CSE", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "CSE" in item["department"].upper()

def test_list_at_risk_students(client, auth_headers):
    response = client.get("/api/students/at-risk", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    for item in data["items"]:
        assert item["risk_level"] in ["High Risk", "Moderate Risk"]

def test_get_student_detail_success(client, auth_headers):
    # First get a student_id from list
    list_res = client.get("/api/students?page_size=1", headers=auth_headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    if len(items) > 0:
        target_id = items[0]["student_id"]
        detail_res = client.get(f"/api/students/{target_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["student_id"] == target_id
        assert "courses" in detail
        assert isinstance(detail["courses"], list)

def test_get_student_detail_not_found(client, auth_headers):
    response = client.get("/api/students/999999999", headers=auth_headers)
    assert response.status_code == 404
