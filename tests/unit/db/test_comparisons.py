"""Tests for saved comparisons CRUD operations."""

import uuid

from axiom.core.db import Database
from axiom.core.models import ComparisonToken, SavedComparison, UserProfile, eet_now


def _make_comparison(user_id: str) -> SavedComparison:
    return SavedComparison(
        comparison_id=str(uuid.uuid4()),
        user_id=user_id,
        name="Comparison",
        created_at=eet_now(),
        updated_at=eet_now(),
    )


def test_create_comparison(user_db: Database) -> None:
    """Test creating a new comparison."""
    profile = UserProfile(
        user_id="user-123",
        email="test@example.com",
        created_at=eet_now(),
    )
    comparison = _make_comparison("user-123")

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_comparison(comparison)

        result = user_db.get_comparison(comparison.comparison_id)

    assert result is not None
    assert result["name"] == "Comparison"


def test_update_comparison(user_db: Database) -> None:
    """Test updating a comparison."""
    profile = UserProfile(
        user_id="user-456",
        email="test@example.com",
        created_at=eet_now(),
    )
    comparison = _make_comparison("user-456")

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_comparison(comparison)

        comparison.name = "Updated Comparison"
        comparison.description = "New description"
        comparison.updated_at = eet_now()

        user_db.update_comparison(comparison)
        result = user_db.get_comparison(comparison.comparison_id)

    assert result is not None
    assert result["name"] == "Updated Comparison"
    assert result["description"] == "New description"


def test_delete_comparison(user_db: Database) -> None:
    """Test deleting a comparison."""
    profile = UserProfile(
        user_id="user-789",
        email="test@example.com",
        created_at=eet_now(),
    )
    comparison = _make_comparison("user-789")

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_comparison(comparison)

        assert user_db.get_comparison(comparison.comparison_id) is not None

        user_db.delete_comparison(comparison.comparison_id)

        assert user_db.get_comparison(comparison.comparison_id) is None


def test_list_comparisons(user_db: Database) -> None:
    """Test listing user's comparisons."""
    profile = UserProfile(
        user_id="user-111",
        email="test@example.com",
        created_at=eet_now(),
    )

    comparison1 = _make_comparison("user-111")
    comparison2 = _make_comparison("user-111")

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_comparison(comparison1)
        user_db.create_comparison(comparison2)

        comparisons = user_db.list_comparisons("user-111")

    assert len(comparisons) == 2
    ids = {c["comparison_id"] for c in comparisons}
    assert ids == {comparison1.comparison_id, comparison2.comparison_id}


def test_add_comparison_token(user_db: Database) -> None:
    """Test adding tokens to a comparison."""
    profile = UserProfile(
        user_id="user-222",
        email="test@example.com",
        created_at=eet_now(),
    )
    comparison = _make_comparison("user-222")

    token = ComparisonToken(
        comparison_id=comparison.comparison_id,
        ca="token-alpha",
        chain="sol",
        position=1,
        added_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_comparison(comparison)
        user_db.add_comparison_token(token)

        tokens = user_db.list_comparison_tokens(comparison.comparison_id)

    assert len(tokens) == 1
    assert tokens[0]["ca"] == "token-alpha"
    assert tokens[0]["position"] == 1


def test_remove_comparison_token(user_db: Database) -> None:
    """Test removing a token from a comparison."""
    profile = UserProfile(
        user_id="user-333",
        email="test@example.com",
        created_at=eet_now(),
    )
    comparison = _make_comparison("user-333")

    token = ComparisonToken(
        comparison_id=comparison.comparison_id,
        ca="token-beta",
        chain="sol",
        position=1,
        added_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_comparison(comparison)
        user_db.add_comparison_token(token)
        assert len(user_db.list_comparison_tokens(comparison.comparison_id)) == 1

        user_db.remove_comparison_token(comparison.comparison_id, "token-beta")

        tokens_after = user_db.list_comparison_tokens(comparison.comparison_id)
        assert len(tokens_after) == 0


def test_comparison_token_unique_constraint(user_db: Database) -> None:
    """Test that comparison token deduplication works (comparison_id + ca + chain)."""
    profile = UserProfile(
        user_id="user-444",
        email="test@example.com",
        created_at=eet_now(),
    )
    comparison = _make_comparison("user-444")

    token1 = ComparisonToken(
        comparison_id=comparison.comparison_id,
        ca="token-gamma",
        chain="sol",
        position=1,
        added_at=eet_now(),
    )

    token2 = ComparisonToken(
        comparison_id=comparison.comparison_id,
        ca="token-gamma",
        chain="sol",
        position=2,
        added_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_comparison(comparison)
        user_db.add_comparison_token(token1)
        user_db.add_comparison_token(token2)

        tokens = user_db.list_comparison_tokens(comparison.comparison_id)

    assert len(tokens) == 1
    assert tokens[0]["position"] == 2


def test_comparison_cascade_delete(user_db: Database) -> None:
    """Test that deleting a comparison cascades to its tokens."""
    profile = UserProfile(
        user_id="user-555",
        email="test@example.com",
        created_at=eet_now(),
    )
    comparison = _make_comparison("user-555")

    token = ComparisonToken(
        comparison_id=comparison.comparison_id,
        ca="token-delta",
        chain="sol",
        position=1,
        added_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_comparison(comparison)
        user_db.add_comparison_token(token)
        assert len(user_db.list_comparison_tokens(comparison.comparison_id)) == 1

        user_db.delete_comparison(comparison.comparison_id)

        tokens_after = user_db.list_comparison_tokens(comparison.comparison_id)
        assert len(tokens_after) == 0
