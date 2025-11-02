"""Tests for search router endpoints."""

from fastapi.testclient import TestClient


def test_search_local_results_only(client: TestClient) -> None:
    """Test search endpoint with local database results."""
    response = client.get("/search?q=test&chain=sol&limit=5&include_external=false")
    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "test"
    assert data["count"] >= 1
    assert "local" in data["sources"]
    assert data["results"][0]["source"] == "local"


def test_search_includes_external(client: TestClient, mock_moralis) -> None:
    """Test search endpoint merging external Moralis results."""
    response = client.get("/search?q=moralis&chain=sol&limit=5&include_external=true")
    assert response.status_code == 200

    data = response.json()
    assert "moralis" in data["sources"]
    addresses = [result["ca"] for result in data["results"]]
    assert "moralis123" in addresses


def test_search_query_validation(client: TestClient) -> None:
    """Test query parameter validation for search endpoint."""
    # Missing query parameter
    response = client.get("/search")
    assert response.status_code == 422

    # Query too short
    response = client.get("/search?q=&chain=sol")
    assert response.status_code == 422

    # Limit too high
    response = client.get("/search?q=test&limit=1000")
    assert response.status_code == 422
