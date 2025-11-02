"""Tests for user router endpoints (protected)."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_add_favorite(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test POST /user/favorites endpoint."""
    response = client.post(
        "/user/favorites",
        json={"ca": "test123abc", "chain": "sol"},
        headers={"Authorization": auth_token},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["ca"] == "test123abc"
    assert data["chain"] == "sol"
    assert data["user_id"] == "test-user-123"


def test_list_favorites(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test GET /user/favorites endpoint."""
    # Add a favorite first
    client.post(
        "/user/favorites",
        json={"ca": "test123abc", "chain": "sol"},
        headers={"Authorization": auth_token},
    )

    # List favorites
    response = client.get("/user/favorites", headers={"Authorization": auth_token})
    assert response.status_code == 200

    data = response.json()
    assert "favorites" in data
    assert data["count"] >= 1


def test_remove_favorite(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test DELETE /user/favorites/{ca} endpoint."""
    # Add a favorite first
    client.post(
        "/user/favorites",
        json={"ca": "test123abc", "chain": "sol"},
        headers={"Authorization": auth_token},
    )

    # Remove favorite
    response = client.delete(
        "/user/favorites/test123abc?chain=sol", headers={"Authorization": auth_token}
    )
    assert response.status_code == 204


def test_create_comparison(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test POST /user/comparisons endpoint."""
    response = client.post(
        "/user/comparisons",
        json={
            "name": "My Comparison",
            "token_addresses": ["test123abc", "test456def"],
            "chain": "sol",
        },
        headers={"Authorization": auth_token},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "My Comparison"
    assert len(data["token_addresses"]) == 2
    assert data["user_id"] == "test-user-123"


def test_list_comparisons(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test GET /user/comparisons endpoint."""
    # Create a comparison first
    client.post(
        "/user/comparisons",
        json={
            "name": "Test Comparison",
            "token_addresses": ["test123abc", "test456def"],
            "chain": "sol",
        },
        headers={"Authorization": auth_token},
    )

    # List comparisons
    response = client.get("/user/comparisons", headers={"Authorization": auth_token})
    assert response.status_code == 200

    data = response.json()
    assert "comparisons" in data
    assert data["count"] >= 1


def test_delete_comparison(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test DELETE /user/comparisons/{comparison_id} endpoint."""
    # Create a comparison first
    create_response = client.post(
        "/user/comparisons",
        json={
            "name": "Test Comparison",
            "token_addresses": ["test123abc", "test456def"],
            "chain": "sol",
        },
        headers={"Authorization": auth_token},
    )
    comparison_id = create_response.json()["comparison_id"]

    # Delete comparison
    response = client.delete(
        f"/user/comparisons/{comparison_id}", headers={"Authorization": auth_token}
    )
    assert response.status_code == 204


def test_create_alert(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test POST /user/alerts endpoint."""
    response = client.post(
        "/user/alerts",
        json={
            "ca": "test123abc",
            "chain": "sol",
            "alert_type": "price_change",
            "threshold": 10.0,
            "enabled": True,
        },
        headers={"Authorization": auth_token},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["ca"] == "test123abc"
    assert data["alert_type"] == "price_change"
    assert data["threshold"] == 10.0


def test_list_alerts(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test GET /user/alerts endpoint."""
    # Create an alert first
    client.post(
        "/user/alerts",
        json={
            "ca": "test123abc",
            "chain": "sol",
            "alert_type": "price_change",
            "threshold": 10.0,
        },
        headers={"Authorization": auth_token},
    )

    # List alerts
    response = client.get("/user/alerts", headers={"Authorization": auth_token})
    assert response.status_code == 200

    data = response.json()
    assert "alerts" in data
    assert data["count"] >= 1


def test_update_alert(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test PATCH /user/alerts/{alert_id} endpoint."""
    # Create an alert first
    create_response = client.post(
        "/user/alerts",
        json={
            "ca": "test123abc",
            "chain": "sol",
            "alert_type": "price_change",
            "threshold": 10.0,
        },
        headers={"Authorization": auth_token},
    )
    alert_id = create_response.json()["alert_id"]

    # Update alert
    response = client.patch(
        f"/user/alerts/{alert_id}",
        json={
            "ca": "test123abc",
            "chain": "sol",
            "alert_type": "volume_spike",
            "threshold": 20.0,
            "enabled": False,
        },
        headers={"Authorization": auth_token},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["alert_type"] == "volume_spike"
    assert data["threshold"] == 20.0
    assert data["enabled"] is False


def test_delete_alert(client: TestClient, auth_token: str, mock_jwt_decode: MagicMock) -> None:
    """Test DELETE /user/alerts/{alert_id} endpoint."""
    # Create an alert first
    create_response = client.post(
        "/user/alerts",
        json={
            "ca": "test123abc",
            "chain": "sol",
            "alert_type": "price_change",
            "threshold": 10.0,
        },
        headers={"Authorization": auth_token},
    )
    alert_id = create_response.json()["alert_id"]

    # Delete alert
    response = client.delete(f"/user/alerts/{alert_id}", headers={"Authorization": auth_token})
    assert response.status_code == 204


def test_unauthorized_access(client: TestClient) -> None:
    """Test endpoints require authentication."""
    # Test favorites without auth
    response = client.get("/user/favorites")
    assert response.status_code == 401

    # Test comparisons without auth
    response = client.get("/user/comparisons")
    assert response.status_code == 401

    # Test alerts without auth
    response = client.get("/user/alerts")
    assert response.status_code == 401
