"""Tests for user profile CRUD operations."""

import json

from axiom.core.db import Database
from axiom.core.models import UserProfile, eet_now


def test_create_user_profile(user_db: Database) -> None:
    """Test creating a new user profile."""
    profile = UserProfile(
        user_id="user-123",
        email="test@example.com",
        display_name="Test User",
        avatar_url="https://example.com/avatar.jpg",
        created_at=eet_now(),
        last_login_at=eet_now(),
        preferences_json=json.dumps({"theme": "dark"}),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        result = user_db.get_user_profile("user-123")

    assert result is not None
    assert result["user_id"] == "user-123"
    assert result["email"] == "test@example.com"
    assert result["display_name"] == "Test User"


def test_update_user_profile(user_db: Database) -> None:
    """Test updating an existing user profile."""
    profile = UserProfile(
        user_id="user-456",
        email="original@example.com",
        display_name="Original Name",
        created_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)

        profile.email = "updated@example.com"
        profile.display_name = "Updated Name"
        profile.last_login_at = eet_now()

        user_db.upsert_user_profile(profile)
        result = user_db.get_user_profile("user-456")

    assert result is not None
    assert result["email"] == "updated@example.com"
    assert result["display_name"] == "Updated Name"


def test_delete_user_profile(user_db: Database) -> None:
    """Test deleting a user profile."""
    profile = UserProfile(
        user_id="user-789",
        email="delete@example.com",
        created_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        assert user_db.get_user_profile("user-789") is not None

        user_db.delete_user_profile("user-789")
        assert user_db.get_user_profile("user-789") is None


def test_get_nonexistent_profile(user_db: Database) -> None:
    """Test getting a profile that doesn't exist."""
    with user_db:
        result = user_db.get_user_profile("nonexistent-user")

    assert result is None
