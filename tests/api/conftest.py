"""Pytest fixtures for API tests."""

import importlib
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import duckdb
import pytest
from fastapi.testclient import TestClient

import services.api.main as main_module
from axiom.core.models import eet_now
from services.api.config import settings


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as f:
        db_path = f.name

    # Initialize database schema
    conn = duckdb.connect(db_path)

    # Create tables
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id VARCHAR PRIMARY KEY,
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            mode VARCHAR,
            config_json VARCHAR,
            config_hash VARCHAR,
            status VARCHAR,
            source_version VARCHAR,
            error_count INTEGER,
            items_inserted INTEGER,
            items_deduped INTEGER,
            events_inserted INTEGER,
            events_deduped INTEGER,
            duration_ms INTEGER
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pulse_items (
            run_id VARCHAR NOT NULL,
            ca VARCHAR NOT NULL,
            segment VARCHAR NOT NULL,
            floor_minute TIMESTAMP NOT NULL,
            floor_price DOUBLE,
            token_name VARCHAR,
            symbol VARCHAR,
            source VARCHAR NOT NULL,
            raw_json VARCHAR,
            scraped_at TIMESTAMP NOT NULL,
            UNIQUE (ca, segment, floor_minute)
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tracker_events (
            run_id VARCHAR NOT NULL,
            wallet VARCHAR NOT NULL,
            ca VARCHAR NOT NULL,
            action VARCHAR NOT NULL,
            tx_time TIMESTAMP NOT NULL,
            tx_sig VARCHAR,
            amount DOUBLE,
            amount_unit VARCHAR,
            price DOUBLE,
            src_url VARCHAR,
            source VARCHAR NOT NULL,
            raw_json VARCHAR,
            scraped_at TIMESTAMP NOT NULL,
            UNIQUE (wallet, ca, action, tx_time)
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            ca VARCHAR NOT NULL,
            chain VARCHAR NOT NULL,
            token_name VARCHAR,
            symbol VARCHAR,
            first_seen_at TIMESTAMP,
            last_seen_at TIMESTAMP,
            last_pulse_at TIMESTAMP,
            last_tracker_at TIMESTAMP,
            latest_segment VARCHAR,
            latest_floor_price DOUBLE,
            PRIMARY KEY (ca, chain)
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS token_metrics (
            ca VARCHAR NOT NULL,
            chain VARCHAR NOT NULL,
            as_of TIMESTAMP NOT NULL,
            score DOUBLE,
            price_usd DOUBLE,
            price_change_1h DOUBLE,
            price_change_6h DOUBLE,
            volume_usd_1h DOUBLE,
            volume_usd_6h DOUBLE,
            volume_usd_24h DOUBLE,
            trade_count_1h INTEGER,
            trade_count_6h INTEGER,
            trade_count_24h INTEGER,
            buy_sell_ratio DOUBLE,
            liquidity_score DOUBLE,
            risk_flags VARCHAR,
            sparkline VARCHAR,
            PRIMARY KEY (ca, chain)
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS token_summaries (
            ca VARCHAR NOT NULL,
            chain VARCHAR NOT NULL,
            as_of TIMESTAMP NOT NULL,
            headline VARCHAR,
            bullet_1 VARCHAR,
            bullet_2 VARCHAR,
            bullet_3 VARCHAR,
            bullet_4 VARCHAR,
            bullet_5 VARCHAR,
            sentiment VARCHAR,
            PRIMARY KEY (ca, chain)
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id VARCHAR PRIMARY KEY,
            email VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_favorites (
            user_id VARCHAR NOT NULL,
            ca VARCHAR NOT NULL,
            chain VARCHAR NOT NULL,
            favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, ca, chain)
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_comparisons (
            comparison_id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            token_addresses VARCHAR NOT NULL,
            chain VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_alerts (
            alert_id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            ca VARCHAR NOT NULL,
            chain VARCHAR NOT NULL,
            alert_type VARCHAR NOT NULL,
            threshold DOUBLE,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_triggered_at TIMESTAMP
        );
        """
    )

    # Insert sample data
    now = eet_now()
    conn.execute(
        """
        INSERT INTO tokens (ca, chain, token_name, symbol, first_seen_at, last_seen_at, latest_floor_price)
        VALUES ('test123abc', 'sol', 'Test Token', 'TEST', ?, ?, 1.5)
        """,
        [now, now],
    )

    conn.execute(
        """
        INSERT INTO token_metrics (ca, chain, as_of, score, price_usd, volume_usd_24h, risk_flags, sparkline)
        VALUES ('test123abc', 'sol', ?, 85.5, 1.5, 100000.0, '[]', NULL)
        """,
        [now],
    )

    conn.execute(
        """
        INSERT INTO token_summaries (ca, chain, as_of, headline, sentiment)
        VALUES ('test123abc', 'sol', ?, 'Test token showing strong momentum', 'positive')
        """,
        [now],
    )

    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def client(temp_db: str) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with temp database."""
    # Backup original settings
    original_path = settings.database_path
    original_redis = settings.redis_url
    original_moralis_key = settings.moralis_api_key
    original_jwt_secret = settings.supabase_jwt_secret

    # Override settings for tests
    settings.database_path = temp_db
    settings.redis_url = "redis://localhost:0/0"  # Force connection failure for fallback
    settings.moralis_api_key = "test-key"
    settings.supabase_jwt_secret = "test-secret"

    # Reload main module to pick up new settings
    importlib.reload(main_module)
    from services.api.main import app

    with TestClient(app) as test_client:
        yield test_client

    # Restore original settings
    settings.database_path = original_path
    settings.redis_url = original_redis
    settings.moralis_api_key = original_moralis_key
    settings.supabase_jwt_secret = original_jwt_secret

    importlib.reload(main_module)


@pytest.fixture
def mock_moralis() -> Generator[AsyncMock, None, None]:
    """Mock Moralis API responses."""
    with patch("services.api.external.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(
            return_value=[
                {
                    "address": "moralis123",
                    "name": "Moralis Token",
                    "symbol": "MOR",
                    "price_usd": 2.5,
                    "volume_24h": 50000.0,
                }
            ]
        )
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def auth_token() -> str:
    """Generate test auth token."""
    return "Bearer test_token_123"


@pytest.fixture
def mock_jwt_decode() -> Generator[MagicMock, None, None]:
    """Mock JWT decode for authentication."""
    with patch("services.api.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "role": "authenticated",
        }
        yield mock_decode
