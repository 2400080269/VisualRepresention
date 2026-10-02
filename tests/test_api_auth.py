"""
Unit and integration tests for Authentication API endpoints (Phase 3).
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def unique_user():
    uid = uuid.uuid4().hex[:8]
    return {
        "username": f"user_{uid}",
        "email": f"user_{uid}@example.com",
        "password": "SecurePassword123!",
        "role": "USER"
    }

def test_register_user_success(client, unique_user):
    response = client.post("/api/auth/register", json=unique_user)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == unique_user["username"]
    assert data["email"] == unique_user["email"]
    assert data["role"] == "USER"
    assert "id" in data
    assert "hashed_password" not in data

def test_register_duplicate_username(client, unique_user):
    # First registration
    client.post("/api/auth/register", json=unique_user)
    # Duplicate attempt
    dup = unique_user.copy()
    dup["email"] = "different_email@example.com"
    response = client.post("/api/auth/register", json=dup)
    assert response.status_code == 400
    assert "already taken" in response.json()["error"]

def test_register_validation_short_password(client):
    invalid_data = {
        "username": "shortpwduser",
        "email": "short@example.com",
        "password": "123",  # Less than 6 chars
        "role": "USER"
    }
    response = client.post("/api/auth/register", json=invalid_data)
    assert response.status_code == 422

def test_login_success(client, unique_user):
    # Register first
    client.post("/api/auth/register", json=unique_user)

    # Login
    login_data = {
        "username_or_email": unique_user["username"],
        "password": unique_user["password"]
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == unique_user["username"]

def test_login_invalid_credentials(client, unique_user):
    client.post("/api/auth/register", json=unique_user)
    login_data = {
        "username_or_email": unique_user["username"],
        "password": "WrongPassword999"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401

def test_get_current_user_me_authenticated(client, unique_user):
    client.post("/api/auth/register", json=unique_user)
    login_res = client.post("/api/auth/login", json={
        "username_or_email": unique_user["username"],
        "password": unique_user["password"]
    })
    token = login_res.json()["access_token"]

    # Call /api/auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["username"] == unique_user["username"]
    assert data["email"] == unique_user["email"]

def test_get_current_user_me_unauthorized(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
