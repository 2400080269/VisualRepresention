"""
Tests for Dataset upload, validation, and quality summary APIs (Phase 4).
"""

import io
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
        "username": f"data_user_{uid}",
        "email": f"data_user_{uid}@example.com",
        "password": "ValidPassword123!",
        "role": "ADMIN"
    }
    client.post("/api/auth/register", json=user_data)
    login_res = client.post("/api/auth/login", json={
        "username_or_email": user_data["username"],
        "password": user_data["password"]
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_upload_invalid_extension(client, auth_headers):
    fake_file = io.BytesIO(b"malicious script")
    response = client.post(
        "/api/datasets/upload",
        headers=auth_headers,
        files={"file": ("malicious.exe", fake_file, "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["error"]

def test_upload_unauthorized(client):
    fake_file = io.BytesIO(b"id,name\n1,Test")
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("students.csv", fake_file, "text/csv")}
    )
    assert response.status_code == 401

def test_upload_valid_csv_and_inspection(client, auth_headers):
    # Sample clean test dataset
    csv_content = (
        "student_id,name,department,year,section,gender,subject,internal,mid1,mid2,assignment,final,total_classes,attended\n"
        "9001,Alice Smith,CSE,3,A,Female,Python,18,22,23,9,85,50,45\n"
        "9002,Bob Jones,CSE,3,A,Male,Python,12,14,15,6,50,50,30\n"
        "9003,Charlie Ray,ECE,3,B,Male,Python,19,24,25,10,92,50,48\n"
    ).encode("utf-8")

    file_obj = io.BytesIO(csv_content)
    response = client.post(
        "/api/datasets/upload",
        headers=auth_headers,
        files={"file": ("test_batch.csv", file_obj, "text/csv")}
    )
    assert response.status_code == 201
    summary = response.json()
    assert "dataset_id" in summary
    assert summary["total_students"] == 3
    assert summary["average_marks"] > 0
    assert "audit_log" in summary

    dataset_id = summary["dataset_id"]

    # Test GET /api/datasets
    list_res = client.get("/api/datasets", headers=auth_headers)
    assert list_res.status_code == 200
    datasets = list_res.json()
    assert any(d["dataset_id"] == dataset_id for d in datasets)

    # Test GET /api/datasets/{dataset_id}
    detail_res = client.get(f"/api/datasets/{dataset_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["dataset_id"] == dataset_id
