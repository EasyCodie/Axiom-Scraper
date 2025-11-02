"""Tests for health check endpoint."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "cache" in data
    assert "timestamp" in data


def test_root_endpoint(client: TestClient) -> None:
    """Test GET / endpoint."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "service" in data
    assert data["service"] == "Axiom Token Analytics API"
    assert "version" in data
    assert "docs" in data
