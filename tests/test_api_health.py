"""
Tests for FastAPI base and health diagnostics (Phase 1).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "version" in data
    assert data["docs_url"] == "/docs"

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "machine_learning" in data

def test_404_handler(client):
    response = client.get("/non_existent_route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["status_code"] == 404
