"""Tests for database helper methods with analytics tables."""

from pathlib import Path

import pytest

from axiom.core.db import Database
from scripts.init_db import init_database


@pytest.fixture()
def empty_analytics_db(tmp_path: Path) -> Database:
    """Initialize an empty analytics database."""
    db_path = tmp_path / "empty_analytics.duckdb"
    init_database(str(db_path))
    return Database(str(db_path))


def test_list_tokens_returns_empty_when_no_data(empty_analytics_db: Database) -> None:
    """list_tokens should return an empty list if the tokens table is empty."""
    with empty_analytics_db:
        tokens = empty_analytics_db.list_tokens(chain="sol")
        assert tokens == []


def test_get_token_returns_none_when_not_found(empty_analytics_db: Database) -> None:
    """get_token should return None if the token doesn't exist."""
    with empty_analytics_db:
        token = empty_analytics_db.get_token("nonexistent-token", chain="sol")
        assert token is None


def test_get_token_pulse_returns_empty_when_no_pulse_data(empty_analytics_db: Database) -> None:
    """get_token_pulse should return an empty list if no pulse data exists for the token."""
    with empty_analytics_db:
        pulse = empty_analytics_db.get_token_pulse("some-token", chain="sol")
        assert pulse == []


def test_get_token_trackers_returns_default_summary_when_no_data(
    empty_analytics_db: Database,
) -> None:
    """get_token_trackers should return a default summary when no tracker data exists."""
    with empty_analytics_db:
        tracker = empty_analytics_db.get_token_trackers("some-token", chain="sol")
        assert tracker["trade_count"] == 0
        assert tracker["unique_wallets"] == 0


def test_get_price_history_returns_empty_when_no_history(empty_analytics_db: Database) -> None:
    """get_price_history should return an empty list when no price history exists."""
    with empty_analytics_db:
        history = empty_analytics_db.get_price_history("some-token", chain="sol")
        assert history == []


def test_get_stats_includes_analytics_tables(empty_analytics_db: Database) -> None:
    """get_stats should include counts for analytics tables."""
    with empty_analytics_db:
        stats = empty_analytics_db.get_stats()
        assert "tokens" in stats
        assert "token_metrics" in stats
        assert stats["tokens"] == 0
        assert stats["token_metrics"] == 0
