"""Tests for watchlist CRUD operations."""

import uuid

from axiom.core.db import Database
from axiom.core.models import UserProfile, Watchlist, WatchlistToken, eet_now


def test_create_watchlist(user_db: Database) -> None:
    """Test creating a new watchlist."""
    profile = UserProfile(
        user_id="user-123",
        email="test@example.com",
        created_at=eet_now(),
    )

    watchlist = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-123",
        name="My Watchlist",
        description="Tracking promising tokens",
        created_at=eet_now(),
        updated_at=eet_now(),
        is_public=False,
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_watchlist(watchlist)

        result = user_db.get_watchlist(watchlist.watchlist_id)

    assert result is not None
    assert result["name"] == "My Watchlist"
    assert result["description"] == "Tracking promising tokens"
    assert result["is_public"] is False


def test_update_watchlist(user_db: Database) -> None:
    """Test updating a watchlist."""
    profile = UserProfile(
        user_id="user-456",
        email="test@example.com",
        created_at=eet_now(),
    )

    watchlist = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-456",
        name="Original Name",
        created_at=eet_now(),
        updated_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_watchlist(watchlist)

        watchlist.name = "Updated Name"
        watchlist.description = "New description"
        watchlist.updated_at = eet_now()

        user_db.update_watchlist(watchlist)
        result = user_db.get_watchlist(watchlist.watchlist_id)

    assert result is not None
    assert result["name"] == "Updated Name"
    assert result["description"] == "New description"


def test_delete_watchlist(user_db: Database) -> None:
    """Test deleting a watchlist."""
    profile = UserProfile(
        user_id="user-789",
        email="test@example.com",
        created_at=eet_now(),
    )

    watchlist = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-789",
        name="Delete Me",
        created_at=eet_now(),
        updated_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_watchlist(watchlist)

        assert user_db.get_watchlist(watchlist.watchlist_id) is not None

        user_db.delete_watchlist(watchlist.watchlist_id)

        assert user_db.get_watchlist(watchlist.watchlist_id) is None


def test_list_watchlists(user_db: Database) -> None:
    """Test listing user's watchlists."""
    profile = UserProfile(
        user_id="user-111",
        email="test@example.com",
        created_at=eet_now(),
    )

    watchlist1 = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-111",
        name="Watchlist 1",
        created_at=eet_now(),
        updated_at=eet_now(),
    )

    watchlist2 = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-111",
        name="Watchlist 2",
        created_at=eet_now(),
        updated_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_watchlist(watchlist1)
        user_db.create_watchlist(watchlist2)

        watchlists = user_db.list_watchlists("user-111")

    assert len(watchlists) == 2
    names = {w["name"] for w in watchlists}
    assert names == {"Watchlist 1", "Watchlist 2"}


def test_add_watchlist_token(user_db: Database) -> None:
    """Test adding tokens to a watchlist."""
    profile = UserProfile(
        user_id="user-222",
        email="test@example.com",
        created_at=eet_now(),
    )

    watchlist = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-222",
        name="Test Watchlist",
        created_at=eet_now(),
        updated_at=eet_now(),
    )

    token = WatchlistToken(
        watchlist_id=watchlist.watchlist_id,
        ca="token-alpha",
        chain="sol",
        added_at=eet_now(),
        position=1,
        notes="Top pick",
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_watchlist(watchlist)
        user_db.add_watchlist_token(token)

        tokens = user_db.list_watchlist_tokens(watchlist.watchlist_id)

    assert len(tokens) == 1
    assert tokens[0]["ca"] == "token-alpha"
    assert tokens[0]["position"] == 1
    assert tokens[0]["notes"] == "Top pick"


def test_remove_watchlist_token(user_db: Database) -> None:
    """Test removing a token from a watchlist."""
    profile = UserProfile(
        user_id="user-333",
        email="test@example.com",
        created_at=eet_now(),
    )

    watchlist = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-333",
        name="Test Watchlist",
        created_at=eet_now(),
        updated_at=eet_now(),
    )

    token = WatchlistToken(
        watchlist_id=watchlist.watchlist_id,
        ca="token-beta",
        chain="sol",
        added_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_watchlist(watchlist)
        user_db.add_watchlist_token(token)

        tokens_before = user_db.list_watchlist_tokens(watchlist.watchlist_id)
        assert len(tokens_before) == 1

        user_db.remove_watchlist_token(watchlist.watchlist_id, "token-beta")

        tokens_after = user_db.list_watchlist_tokens(watchlist.watchlist_id)
        assert len(tokens_after) == 0


def test_watchlist_cascade_delete(user_db: Database) -> None:
    """Test that deleting a watchlist cascades to its tokens."""
    profile = UserProfile(
        user_id="user-444",
        email="test@example.com",
        created_at=eet_now(),
    )

    watchlist = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-444",
        name="Test Watchlist",
        created_at=eet_now(),
        updated_at=eet_now(),
    )

    token = WatchlistToken(
        watchlist_id=watchlist.watchlist_id,
        ca="token-gamma",
        chain="sol",
        added_at=eet_now(),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_watchlist(watchlist)
        user_db.add_watchlist_token(token)

        tokens_before = user_db.list_watchlist_tokens(watchlist.watchlist_id)
        assert len(tokens_before) == 1

        user_db.delete_watchlist(watchlist.watchlist_id)

        tokens_after = user_db.list_watchlist_tokens(watchlist.watchlist_id)
        assert len(tokens_after) == 0


def test_watchlist_token_unique_constraint(user_db: Database) -> None:
    """Test that watchlist token deduplication works (watchlist_id + ca + chain)."""
    profile = UserProfile(
        user_id="user-555",
        email="test@example.com",
        created_at=eet_now(),
    )

    watchlist = Watchlist(
        watchlist_id=str(uuid.uuid4()),
        user_id="user-555",
        name="Test Watchlist",
        created_at=eet_now(),
        updated_at=eet_now(),
    )

    token1 = WatchlistToken(
        watchlist_id=watchlist.watchlist_id,
        ca="token-delta",
        chain="sol",
        added_at=eet_now(),
        position=1,
        notes="First note",
    )

    token2 = WatchlistToken(
        watchlist_id=watchlist.watchlist_id,
        ca="token-delta",
        chain="sol",
        added_at=eet_now(),
        position=2,
        notes="Updated note",
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_watchlist(watchlist)
        user_db.add_watchlist_token(token1)
        user_db.add_watchlist_token(token2)

        tokens = user_db.list_watchlist_tokens(watchlist.watchlist_id)

    assert len(tokens) == 1
    assert tokens[0]["position"] == 2
    assert tokens[0]["notes"] == "Updated note"
