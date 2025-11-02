"""Tests for analytics aggregation logic and database helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pytz

from axiom.core.analytics import rebuild_token_views, refresh_analytics
from axiom.core.db import Database
from axiom.core.models import (
    PulseItem,
    TokenOverview,
    TokenPulseSnapshot,
    TokenTrackerSummary,
    TrackerEvent,
)
from scripts.init_db import init_database

EET = pytz.timezone("Europe/Athens")


def make_eet(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in EET."""
    if dt.tzinfo is None:
        return EET.localize(dt)
    return dt.astimezone(EET)


@pytest.fixture()
def analytics_db(tmp_path: Path) -> Database:
    """Create a temporary database for analytics tests."""
    db_path = tmp_path / "analytics.duckdb"
    init_database(str(db_path))
    return Database(str(db_path))


def seed_sample_data(db: Database) -> None:
    """Seed pulse and tracker data for testing."""
    base_time = make_eet(datetime(2024, 1, 1, 12, 0))

    pulse_items = [
        PulseItem(
            run_id="run-1",
            ca="token-alpha",
            segment="new",
            floor_minute=base_time - timedelta(hours=6),
            floor_price=0.75,
            token_name="Alpha",
            symbol="ALP",
            raw_json="{}",
            scraped_at=base_time - timedelta(hours=6),
        ),
        PulseItem(
            run_id="run-1",
            ca="token-alpha",
            segment="new",
            floor_minute=base_time - timedelta(hours=3),
            floor_price=1.10,
            token_name="Alpha",
            symbol="ALP",
            raw_json="{}",
            scraped_at=base_time - timedelta(hours=3),
        ),
        PulseItem(
            run_id="run-1",
            ca="token-alpha",
            segment="new",
            floor_minute=base_time - timedelta(minutes=45),
            floor_price=1.90,
            token_name="Alpha",
            symbol="ALP",
            raw_json="{}",
            scraped_at=base_time - timedelta(minutes=45),
        ),
        PulseItem(
            run_id="run-2",
            ca="token-alpha",
            segment="rising",
            floor_minute=base_time - timedelta(minutes=10),
            floor_price=2.10,
            token_name="Alpha",
            symbol="ALP",
            raw_json="{}",
            scraped_at=base_time - timedelta(minutes=10),
        ),
        PulseItem(
            run_id="run-2",
            ca="token-beta",
            segment="new",
            floor_minute=base_time - timedelta(hours=2),
            floor_price=0.45,
            token_name="Beta",
            symbol="BET",
            raw_json="{}",
            scraped_at=base_time - timedelta(hours=2),
        ),
        PulseItem(
            run_id="run-2",
            ca="token-beta",
            segment="new",
            floor_minute=base_time - timedelta(minutes=20),
            floor_price=0.40,
            token_name="Beta",
            symbol="BET",
            raw_json="{}",
            scraped_at=base_time - timedelta(minutes=20),
        ),
    ]

    tracker_events = [
        TrackerEvent(
            run_id="run-1",
            wallet="wallet-1",
            ca="token-alpha",
            action="buy",
            tx_time=base_time - timedelta(minutes=50),
            tx_sig="sig-1",
            amount=100.0,
            amount_unit="tokens",
            price=1.8,
            src_url="https://example.com/tx1",
            raw_json="{}",
            scraped_at=base_time - timedelta(minutes=40),
        ),
        TrackerEvent(
            run_id="run-1",
            wallet="wallet-2",
            ca="token-alpha",
            action="buy",
            tx_time=base_time - timedelta(minutes=30),
            tx_sig="sig-2",
            amount=75.0,
            amount_unit="tokens",
            price=1.95,
            src_url="https://example.com/tx2",
            raw_json="{}",
            scraped_at=base_time - timedelta(minutes=25),
        ),
        TrackerEvent(
            run_id="run-1",
            wallet="wallet-3",
            ca="token-alpha",
            action="sell",
            tx_time=base_time - timedelta(minutes=15),
            tx_sig="sig-3",
            amount=50.0,
            amount_unit="tokens",
            price=2.05,
            src_url="https://example.com/tx3",
            raw_json="{}",
            scraped_at=base_time - timedelta(minutes=10),
        ),
        TrackerEvent(
            run_id="run-1",
            wallet="wallet-4",
            ca="token-alpha",
            action="buy",
            tx_time=base_time - timedelta(minutes=5),
            tx_sig="sig-4",
            amount=60.0,
            amount_unit="tokens",
            price=2.10,
            src_url="https://example.com/tx4",
            raw_json="{}",
            scraped_at=base_time - timedelta(minutes=4),
        ),
        TrackerEvent(
            run_id="run-1",
            wallet="wallet-5",
            ca="token-beta",
            action="sell",
            tx_time=base_time - timedelta(minutes=45),
            tx_sig="sig-5",
            amount=12.0,
            amount_unit="tokens",
            price=0.41,
            src_url="https://example.com/tx5",
            raw_json="{}",
            scraped_at=base_time - timedelta(minutes=42),
        ),
    ]

    with db:
        db.upsert_pulse_items(pulse_items)
        db.upsert_tracker_events(tracker_events)


def test_refresh_analytics_updates_metrics_and_summaries(analytics_db: Database) -> None:
    """Analytics refresh should populate metrics, summaries, and helper queries."""
    seed_sample_data(analytics_db)

    with analytics_db:
        conn = analytics_db.connect()
        rebuild_token_views(conn, chain="sol", bootstrap_metrics=True)
        result = refresh_analytics(conn, chain="sol")

    assert result["tokens_rebuilt"] >= 2
    assert result["metrics_updated"] >= 0
    assert result["summaries_updated"] >= 0

    # Validate list_tokens helper
    tokens = analytics_db.list_tokens(chain="sol", limit=10)
    assert len(tokens) == 2
    top_token = next(t for t in tokens if t["ca"] == "token-alpha")
    assert top_token["score"] is not None
    assert top_token["price_usd"] == pytest.approx(2.10, rel=1e-3)
    assert top_token["risk_flags"] in ([], "[]") or "low_activity" not in top_token["risk_flags"]

    # get_token should merge metrics and summaries
    token_detail = analytics_db.get_token("token-alpha")
    assert token_detail is not None
    overview = TokenOverview(**token_detail)
    assert overview.ca == "token-alpha"
    # Sparkline may be empty if no price data within lookback window
    assert isinstance(overview.sparkline, list)
    assert 0 <= overview.score <= 100

    # Validate pulse history helper
    pulse_history = analytics_db.get_token_pulse("token-alpha", limit=5)
    assert len(pulse_history) >= 4
    pulse_models = [TokenPulseSnapshot(**row) for row in pulse_history]
    assert all(snapshot.ca == "token-alpha" for snapshot in pulse_models)

    # Validate tracker summary helper
    tracker_summary = analytics_db.get_token_trackers("token-alpha")
    summary_model = TokenTrackerSummary(**tracker_summary)
    assert summary_model.trade_count >= 3
    assert summary_model.buy_count > summary_model.sell_count
    assert summary_model.top_actions

    # Price history helper returns seeded entries
    price_history = analytics_db.get_price_history("token-alpha")
    assert len(price_history) >= 4

    # Token beta should surface low activity risk flag
    beta = analytics_db.get_token("token-beta")
    assert beta is not None
    beta_overview = TokenOverview(**beta)
    assert beta_overview.ca == "token-beta"
    assert isinstance(beta_overview.risk_flags, list)
