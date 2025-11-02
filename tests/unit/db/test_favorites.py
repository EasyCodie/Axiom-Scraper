"""Tests for favorite tokens CRUD operations."""

from axiom.core.db import Database
from axiom.core.models import FavoriteToken, UserProfile, eet_now


def test_add_favorite_token(user_db: Database) -> None:
    """Test adding a token to favorites."""
    profile = UserProfile(
        user_id="user-123",
        email="test@example.com",
        created_at=eet_now(),
    )

    favorite = FavoriteToken(
        user_id="user-123",
        ca="token-alpha",
        chain="sol",
        added_at=eet_now(),
        notes="Interesting project",
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.add_favorite_token(favorite)

        favorites = user_db.list_favorite_tokens("user-123")

    assert len(favorites) == 1
    assert favorites[0]["ca"] == "token-alpha"
    assert favorites[0]["notes"] == "Interesting project"


def test_remove_favorite_token(user_db: Database) -> None:
    """Test removing a token from favorites."""
    profile = UserProfile(
        user_id="user-456",
        email="test@example.com",
        created_at=eet_now(),
    )

    favorite = FavoriteToken(
        user_id="user-456",
        ca="token-beta",
        chain="sol",
        added_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.add_favorite_token(favorite)

        favorites_before = user_db.list_favorite_tokens("user-456")
        assert len(favorites_before) == 1

        user_db.remove_favorite_token("user-456", "token-beta")

        favorites_after = user_db.list_favorite_tokens("user-456")
        assert len(favorites_after) == 0


def test_list_favorite_tokens_empty(user_db: Database) -> None:
    """Test listing favorites for a user with none."""
    profile = UserProfile(
        user_id="user-789",
        email="test@example.com",
        created_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        favorites = user_db.list_favorite_tokens("user-789")

    assert len(favorites) == 0


def test_favorite_token_unique_constraint(user_db: Database) -> None:
    """Test that favorite token deduplication works (user + ca + chain)."""
    profile = UserProfile(
        user_id="user-111",
        email="test@example.com",
        created_at=eet_now(),
    )

    favorite1 = FavoriteToken(
        user_id="user-111",
        ca="token-gamma",
        chain="sol",
        added_at=eet_now(),
        notes="First note",
    )

    favorite2 = FavoriteToken(
        user_id="user-111",
        ca="token-gamma",
        chain="sol",
        added_at=eet_now(),
        notes="Updated note",
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.add_favorite_token(favorite1)
        user_db.add_favorite_token(favorite2)

        favorites = user_db.list_favorite_tokens("user-111")

    assert len(favorites) == 1
    assert favorites[0]["notes"] == "Updated note"


def test_favorite_token_cascade_delete(user_db: Database) -> None:
    """Test that deleting a user cascades to their favorites."""
    profile = UserProfile(
        user_id="user-222",
        email="test@example.com",
        created_at=eet_now(),
    )

    favorite = FavoriteToken(
        user_id="user-222",
        ca="token-delta",
        chain="sol",
        added_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.add_favorite_token(favorite)

        favorites_before = user_db.list_favorite_tokens("user-222")
        assert len(favorites_before) == 1

        user_db.delete_user_profile("user-222")

        favorites_after = user_db.list_favorite_tokens("user-222")
        assert len(favorites_after) == 0
