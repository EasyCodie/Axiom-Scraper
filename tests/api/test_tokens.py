"""Tests for tokens router endpoints."""

from fastapi.testclient import TestClient


def test_list_tokens(client: TestClient) -> None:
    """Test GET /tokens endpoint."""
    response = client.get("/tokens?chain=sol&limit=10&offset=0")
    assert response.status_code == 200

    data = response.json()
    assert "tokens" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert isinstance(data["tokens"], list)


def test_list_tokens_default_params(client: TestClient) -> None:
    """Test GET /tokens with default parameters."""
    response = client.get("/tokens")
    assert response.status_code == 200

    data = response.json()
    assert data["limit"] == 100
    assert data["offset"] == 0


def test_get_token_found(client: TestClient) -> None:
    """Test GET /tokens/{ca} for existing token."""
    response = client.get("/tokens/test123abc?chain=sol")
    assert response.status_code == 200

    data = response.json()
    assert data["ca"] == "test123abc"
    assert data["chain"] == "sol"
    assert data["token_name"] == "Test Token"
    assert data["symbol"] == "TEST"
    assert data["score"] == 85.5
    assert data["price_usd"] == 1.5


def test_get_token_not_found(client: TestClient) -> None:
    """Test GET /tokens/{ca} for non-existent token."""
    response = client.get("/tokens/nonexistent123?chain=sol")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_token_pulse(client: TestClient) -> None:
    """Test GET /tokens/{ca}/pulse endpoint."""
    response = client.get("/tokens/test123abc/pulse?chain=sol&limit=50")
    assert response.status_code == 200

    data = response.json()
    assert "snapshots" in data
    assert "count" in data
    assert isinstance(data["snapshots"], list)


def test_get_token_pulse_not_found(client: TestClient) -> None:
    """Test GET /tokens/{ca}/pulse for non-existent token."""
    response = client.get("/tokens/nonexistent123/pulse?chain=sol")
    assert response.status_code == 404


def test_get_token_trackers(client: TestClient) -> None:
    """Test GET /tokens/{ca}/trackers endpoint."""
    response = client.get("/tokens/test123abc/trackers?chain=sol")
    assert response.status_code == 200

    data = response.json()
    assert "summary" in data
    summary = data["summary"]
    assert "ca" in summary
    assert "chain" in summary
    assert "trade_count" in summary


def test_get_token_trackers_not_found(client: TestClient) -> None:
    """Test GET /tokens/{ca}/trackers for non-existent token."""
    response = client.get("/tokens/nonexistent123/trackers?chain=sol")
    assert response.status_code == 404


def test_list_tokens_pagination(client: TestClient) -> None:
    """Test pagination parameters validation."""
    # Valid pagination
    response = client.get("/tokens?limit=50&offset=10")
    assert response.status_code == 200

    # Invalid limit (too high)
    response = client.get("/tokens?limit=1000")
    assert response.status_code == 422

    # Invalid offset (negative)
    response = client.get("/tokens?offset=-1")
    assert response.status_code == 422
