"""
Database initialization script for DuckDB.

Creates tables with unique constraints for deduplication:
- runs: metadata for each scraper run
- pulse_items: Pulse tokens with (ca, segment, floor_minute) uniqueness
- tracker_events: Tracker events with (wallet, ca, action, tx_time) uniqueness
"""

import sys
from pathlib import Path

import duckdb


def seed_denormalized_tables(conn: duckdb.DuckDBPyConnection, chain: str = "sol") -> None:
    """Seed denormalized analytics tables from existing base tables."""
    try:
        # Clear existing analytic tables for the requested chain
        conn.execute("DELETE FROM token_metrics WHERE chain = ?", [chain])
        conn.execute("DELETE FROM token_summaries WHERE chain = ?", [chain])
        conn.execute("DELETE FROM token_price_history WHERE chain = ?", [chain])
        conn.execute("DELETE FROM tokens WHERE chain = ?", [chain])

        # Build combined token view from pulse and tracker data
        conn.execute(
            """
            WITH pulse AS (
                SELECT
                    ca,
                    MIN(scraped_at) AS first_pulse_at,
                    MAX(scraped_at) AS last_pulse_at,
                    max_by(segment, floor_minute) AS latest_segment,
                    max_by(token_name, floor_minute) AS token_name,
                    max_by(symbol, floor_minute) AS symbol,
                    max_by(floor_price, floor_minute) AS latest_floor_price
                FROM pulse_items
                GROUP BY ca
            ),
            tracker AS (
                SELECT
                    ca,
                    MIN(scraped_at) AS first_tracker_at,
                    MAX(scraped_at) AS last_tracker_at
                FROM tracker_events
                GROUP BY ca
            ),
            ca_union AS (
                SELECT DISTINCT ca FROM pulse_items
                UNION
                SELECT DISTINCT ca FROM tracker_events
            )
            INSERT INTO tokens (
                ca, chain, token_name, symbol, first_seen_at, last_seen_at,
                last_pulse_at, last_tracker_at, latest_segment, latest_floor_price
            )
            SELECT
                cu.ca,
                ? AS chain,
                pulse.token_name,
                pulse.symbol,
                COALESCE(pulse.first_pulse_at, tracker.first_tracker_at) AS first_seen_at,
                COALESCE(pulse.last_pulse_at, tracker.last_tracker_at) AS last_seen_at,
                pulse.last_pulse_at,
                tracker.last_tracker_at,
                pulse.latest_segment,
                pulse.latest_floor_price
            FROM ca_union cu
            LEFT JOIN pulse ON cu.ca = pulse.ca
            LEFT JOIN tracker ON cu.ca = tracker.ca
            WHERE cu.ca IS NOT NULL;
            """,
            [chain],
        )

        # Seed price history directly from pulse snapshots
        conn.execute(
            """
            INSERT INTO token_price_history (
                ca, chain, segment, bucket, floor_price, run_id, scraped_at
            )
            SELECT
                ca,
                ? AS chain,
                segment,
                floor_minute,
                floor_price,
                run_id,
                scraped_at
            FROM pulse_items
            WHERE ca IS NOT NULL AND floor_minute IS NOT NULL;
            """,
            [chain],
        )

        # Initialize metrics and summaries with placeholder values
        conn.execute(
            """
            INSERT INTO token_metrics (
                ca, chain, as_of, score, price_usd, price_change_1h, price_change_6h,
                volume_usd_1h, volume_usd_6h, volume_usd_24h, trade_count_1h,
                trade_count_6h, trade_count_24h, buy_sell_ratio, liquidity_score,
                risk_flags, sparkline
            )
            SELECT
                ca,
                chain,
                COALESCE(last_seen_at, CURRENT_TIMESTAMP),
                NULL,
                latest_floor_price,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                '[]',
                NULL
            FROM tokens
            WHERE chain = ?;
            """,
            [chain],
        )

        conn.execute(
            """
            INSERT INTO token_summaries (
                ca, chain, as_of, headline, bullet_1, bullet_2, bullet_3, bullet_4, bullet_5, sentiment
            )
            SELECT
                ca,
                chain,
                COALESCE(last_seen_at, CURRENT_TIMESTAMP),
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL
            FROM tokens
            WHERE chain = ?;
            """,
            [chain],
        )

        token_count = conn.execute(
            "SELECT COUNT(*) FROM tokens WHERE chain = ?", [chain]
        ).fetchone()[0]
        price_count = conn.execute(
            "SELECT COUNT(*) FROM token_price_history WHERE chain = ?", [chain]
        ).fetchone()[0]
        if token_count or price_count:
            print(
                f"✓ Seeded {token_count} tokens and {price_count} price history rows for chain '{chain}'"
            )
    except duckdb.Error as exc:
        print(f"⚠ Warning: Unable to seed denormalized tables (likely empty base tables): {exc}")


def init_database(db_path: str = "data/axiom.duckdb") -> None:
    """
    Initialize DuckDB database with required schema.

    Args:
        db_path: Path to the DuckDB database file
    """
    # Ensure data directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Initializing database at: {db_path}")

    # Connect to DuckDB
    conn = duckdb.connect(db_path)

    try:
        # Create runs table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id VARCHAR PRIMARY KEY,
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP,
                mode VARCHAR NOT NULL,
                config_json VARCHAR NOT NULL,
                config_hash VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                source_version VARCHAR,
                error_count INTEGER DEFAULT 0,
                items_inserted INTEGER DEFAULT 0,
                items_deduped INTEGER DEFAULT 0,
                events_inserted INTEGER DEFAULT 0,
                events_deduped INTEGER DEFAULT 0,
                duration_ms INTEGER
            );
        """
        )
        print("✓ Created 'runs' table")

        # Create pulse_items table with unique constraint
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
        print("✓ Created 'pulse_items' table")

        # Create indexes for pulse_items
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pulse_ca_minute
            ON pulse_items (ca, floor_minute);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pulse_segment
            ON pulse_items (segment);
        """
        )
        print("✓ Created indexes on 'pulse_items'")

        # Create tracker_events table with unique constraint
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
        print("✓ Created 'tracker_events' table")

        # Create indexes for tracker_events
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trackers_ca_time
            ON tracker_events (ca, tx_time);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trackers_wallet
            ON tracker_events (wallet);
        """
        )
        print("✓ Created indexes on 'tracker_events'")

        # Create tokens table (denormalized view)
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
        print("✓ Created 'tokens' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tokens_ca
            ON tokens (ca);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tokens_chain
            ON tokens (chain);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tokens_last_seen
            ON tokens (last_seen_at);
        """
        )
        print("✓ Created indexes on 'tokens'")

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
                PRIMARY KEY (ca, chain),
                FOREIGN KEY (ca, chain) REFERENCES tokens(ca, chain)
            );
        """
        )
        print("✓ Created 'token_metrics' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_token_metrics_ca
            ON token_metrics (ca);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_token_metrics_chain
            ON token_metrics (chain);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_token_metrics_asof
            ON token_metrics (as_of);
        """
        )
        print("✓ Created indexes on 'token_metrics'")

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
                PRIMARY KEY (ca, chain),
                FOREIGN KEY (ca, chain) REFERENCES tokens(ca, chain)
            );
        """
        )
        print("✓ Created 'token_summaries' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_token_summaries_ca
            ON token_summaries (ca);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_token_summaries_chain
            ON token_summaries (chain);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_token_summaries_asof
            ON token_summaries (as_of);
        """
        )
        print("✓ Created indexes on 'token_summaries'")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS token_price_history (
                ca VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                segment VARCHAR,
                bucket TIMESTAMP NOT NULL,
                floor_price DOUBLE,
                run_id VARCHAR,
                scraped_at TIMESTAMP,
                PRIMARY KEY (ca, chain, segment, bucket),
                FOREIGN KEY (ca, chain) REFERENCES tokens(ca, chain)
            );
        """
        )
        print("✓ Created 'token_price_history' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_price_history_ca
            ON token_price_history (ca);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_price_history_chain
            ON token_price_history (chain);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_price_history_bucket
            ON token_price_history (bucket);
        """
        )
        print("✓ Created indexes on 'token_price_history'")

        # Create user_profiles table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id VARCHAR PRIMARY KEY,
                email VARCHAR,
                display_name VARCHAR,
                avatar_url VARCHAR,
                created_at TIMESTAMP NOT NULL,
                last_login_at TIMESTAMP,
                preferences_json VARCHAR
            );
        """
        )
        print("✓ Created 'user_profiles' table")

        # Create favorite_tokens table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS favorite_tokens (
                user_id VARCHAR NOT NULL,
                ca VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                added_at TIMESTAMP NOT NULL,
                notes VARCHAR,
                PRIMARY KEY (user_id, ca, chain)
            );
        """
        )
        print("✓ Created 'favorite_tokens' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_favorite_tokens_user
            ON favorite_tokens (user_id);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_favorite_tokens_ca
            ON favorite_tokens (ca, chain);
        """
        )
        print("✓ Created indexes on 'favorite_tokens'")

        # Create watchlists table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlists (
                watchlist_id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description VARCHAR,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                is_public BOOLEAN DEFAULT FALSE
            );
        """
        )
        print("✓ Created 'watchlists' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_watchlists_user
            ON watchlists (user_id);
        """
        )
        print("✓ Created indexes on 'watchlists'")

        # Create watchlist_tokens table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist_tokens (
                watchlist_id VARCHAR NOT NULL,
                ca VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                added_at TIMESTAMP NOT NULL,
                position INTEGER,
                notes VARCHAR,
                PRIMARY KEY (watchlist_id, ca, chain)
            );
        """
        )
        print("✓ Created 'watchlist_tokens' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_watchlist_tokens_watchlist
            ON watchlist_tokens (watchlist_id);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_watchlist_tokens_ca
            ON watchlist_tokens (ca, chain);
        """
        )
        print("✓ Created indexes on 'watchlist_tokens'")

        # Create saved_comparisons table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_comparisons (
                comparison_id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description VARCHAR,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            );
        """
        )
        print("✓ Created 'saved_comparisons' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_saved_comparisons_user
            ON saved_comparisons (user_id);
        """
        )
        print("✓ Created indexes on 'saved_comparisons'")

        # Create comparison_tokens table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS comparison_tokens (
                comparison_id VARCHAR NOT NULL,
                ca VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                position INTEGER NOT NULL,
                added_at TIMESTAMP NOT NULL,
                PRIMARY KEY (comparison_id, ca, chain)
            );
        """
        )
        print("✓ Created 'comparison_tokens' table")

        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_comparison_tokens_position
            ON comparison_tokens (comparison_id, position);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_comparison_tokens_ca
            ON comparison_tokens (ca, chain);
        """
        )
        print("✓ Created indexes on 'comparison_tokens'")

        # Create alerts table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                ca VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                alert_type VARCHAR NOT NULL,
                condition_json VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                last_triggered_at TIMESTAMP,
                trigger_count INTEGER DEFAULT 0
            );
        """
        )
        print("✓ Created 'alerts' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_user
            ON alerts (user_id);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_ca
            ON alerts (ca, chain);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_active
            ON alerts (is_active);
        """
        )
        print("✓ Created indexes on 'alerts'")

        # Create alert_channels table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_channels (
                alert_id VARCHAR NOT NULL,
                channel_type VARCHAR NOT NULL,
                channel_config_json VARCHAR NOT NULL,
                is_enabled BOOLEAN DEFAULT TRUE,
                PRIMARY KEY (alert_id, channel_type)
            );
        """
        )
        print("✓ Created 'alert_channels' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_channels_alert
            ON alert_channels (alert_id);
        """
        )
        print("✓ Created indexes on 'alert_channels'")

        # Create alert_events table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_events (
                event_id VARCHAR PRIMARY KEY,
                alert_id VARCHAR NOT NULL,
                triggered_at TIMESTAMP NOT NULL,
                condition_met_json VARCHAR NOT NULL,
                delivery_status VARCHAR NOT NULL,
                delivery_attempts INTEGER DEFAULT 0,
                delivered_at TIMESTAMP,
                error_message VARCHAR
            );
        """
        )
        print("✓ Created 'alert_events' table")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_events_alert
            ON alert_events (alert_id);
        """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alert_events_triggered
            ON alert_events (triggered_at);
        """
        )
        print("✓ Created indexes on 'alert_events'")

        # Seed denormalized tables from existing data
        seed_denormalized_tables(conn)

        # Verify tables
        tables = conn.execute("SHOW TABLES;").fetchall()
        print(f"\n✓ Database initialized successfully with {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

    except Exception as e:
        print(f"✗ Error initializing database: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()

    print(f"\n✓ Database ready at: {db_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize Axiom scraper database")
    parser.add_argument(
        "--db-path", type=str, default="data/axiom.duckdb", help="Path to DuckDB database file"
    )

    args = parser.parse_args()
    init_database(args.db_path)
