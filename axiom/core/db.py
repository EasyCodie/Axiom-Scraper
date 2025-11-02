"""
DuckDB persistence layer with upsert operations for deduplication.

Provides connection management and batch upsert methods for:
- runs: Run metadata
- pulse_items: Pulse token snapshots (dedupe on ca, segment, floor_minute)
- tracker_events: Tracker wallet events (dedupe on wallet, ca, action, tx_time)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import duckdb

from axiom.core.models import PulseItem, RunMeta, TrackerEvent


class Database:
    """DuckDB database connection and operations."""

    def __init__(self, db_path: str = "data/axiom.duckdb"):
        """
        Initialize database connection.

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path
        self._ensure_db_exists()
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def _ensure_db_exists(self) -> None:
        """Ensure database file and directory exist."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> duckdb.DuckDBPyConnection:
        """
        Get or create database connection.

        Returns:
            DuckDB connection object
        """
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
        return self.conn

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # ==================== RUN METADATA ====================

    def create_run(self, run_meta: RunMeta) -> None:
        """
        Create a new run record.

        Args:
            run_meta: Run metadata object
        """
        conn = self.connect()

        conn.execute(
            """
            INSERT INTO runs (
                run_id, started_at, finished_at, mode, config_json, config_hash,
                status, source_version, error_count, items_inserted, items_deduped,
                events_inserted, events_deduped, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run_meta.run_id,
                run_meta.started_at,
                run_meta.finished_at,
                run_meta.mode,
                run_meta.config_json,
                run_meta.config_hash,
                run_meta.status,
                run_meta.source_version,
                run_meta.error_count,
                run_meta.items_inserted,
                run_meta.items_deduped,
                run_meta.events_inserted,
                run_meta.events_deduped,
                run_meta.duration_ms,
            ],
        )

    def update_run(
        self,
        run_id: str,
        finished_at: datetime,
        status: str,
        error_count: int = 0,
        items_inserted: int = 0,
        items_deduped: int = 0,
        events_inserted: int = 0,
        events_deduped: int = 0,
        duration_ms: Optional[int] = None,
    ) -> None:
        """
        Update run record with final statistics.

        Args:
            run_id: Run identifier
            finished_at: Finish timestamp
            status: Final status (success/failed)
            error_count: Number of errors
            items_inserted: Pulse items inserted
            items_deduped: Pulse items deduplicated
            events_inserted: Tracker events inserted
            events_deduped: Tracker events deduplicated
            duration_ms: Run duration in milliseconds
        """
        conn = self.connect()

        conn.execute(
            """
            UPDATE runs
            SET finished_at = ?,
                status = ?,
                error_count = ?,
                items_inserted = ?,
                items_deduped = ?,
                events_inserted = ?,
                events_deduped = ?,
                duration_ms = ?
            WHERE run_id = ?
            """,
            [
                finished_at,
                status,
                error_count,
                items_inserted,
                items_deduped,
                events_inserted,
                events_deduped,
                duration_ms,
                run_id,
            ],
        )

    def get_run(self, run_id: str) -> Optional[dict]:
        """
        Get run record by ID.

        Args:
            run_id: Run identifier

        Returns:
            Run record as dict or None if not found
        """
        conn = self.connect()
        result = conn.execute("SELECT * FROM runs WHERE run_id = ?", [run_id]).fetchone()

        if result:
            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))
        return None

    # ==================== PULSE ITEMS ====================

    def upsert_pulse_items(self, items: List[PulseItem]) -> Tuple[int, int]:
        """
        Batch upsert pulse items with deduplication.

        Deduplication key: (ca, segment, floor_minute)

        Args:
            items: List of PulseItem objects

        Returns:
            Tuple of (inserted_count, deduped_count)
        """
        if not items:
            return 0, 0

        conn = self.connect()

        # Get count before insert
        before_count = conn.execute("SELECT COUNT(*) FROM pulse_items").fetchone()[0]

        # Prepare batch data
        values = [
            (
                item.run_id,
                item.ca,
                item.segment,
                item.floor_minute,
                item.floor_price,
                item.token_name,
                item.symbol,
                item.source,
                item.raw_json,
                item.scraped_at,
            )
            for item in items
        ]

        # Use INSERT OR REPLACE for deduplication
        # DuckDB doesn't support ON CONFLICT, so we delete first then insert
        for item in items:
            conn.execute(
                """
                DELETE FROM pulse_items
                WHERE ca = ? AND segment = ? AND floor_minute = ?
                """,
                [item.ca, item.segment, item.floor_minute],
            )

        # Batch insert
        conn.executemany(
            """
            INSERT INTO pulse_items (
                run_id, ca, segment, floor_minute, floor_price,
                token_name, symbol, source, raw_json, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )

        # Get count after insert
        after_count = conn.execute("SELECT COUNT(*) FROM pulse_items").fetchone()[0]

        inserted_count = len(items)
        deduped_count = inserted_count - (after_count - before_count)

        return inserted_count, deduped_count

    def get_pulse_items(self, run_id: Optional[str] = None, limit: int = 100) -> List[dict]:
        """
        Retrieve pulse items.

        Args:
            run_id: Filter by run ID (optional)
            limit: Maximum number of items to return

        Returns:
            List of pulse item records as dicts
        """
        conn = self.connect()

        if run_id:
            result = conn.execute(
                "SELECT * FROM pulse_items WHERE run_id = ? LIMIT ?", [run_id, limit]
            ).fetchall()
        else:
            result = conn.execute("SELECT * FROM pulse_items LIMIT ?", [limit]).fetchall()

        if result:
            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]
        return []

    # ==================== TRACKER EVENTS ====================

    def upsert_tracker_events(self, events: List[TrackerEvent]) -> Tuple[int, int]:
        """
        Batch upsert tracker events with deduplication.

        Deduplication key: (wallet, ca, action, tx_time)

        Args:
            events: List of TrackerEvent objects

        Returns:
            Tuple of (inserted_count, deduped_count)
        """
        if not events:
            return 0, 0

        conn = self.connect()

        # Get count before insert
        before_count = conn.execute("SELECT COUNT(*) FROM tracker_events").fetchone()[0]

        # Delete existing records with same key
        for event in events:
            conn.execute(
                """
                DELETE FROM tracker_events
                WHERE wallet = ? AND ca = ? AND action = ? AND tx_time = ?
                """,
                [event.wallet, event.ca, event.action, event.tx_time],
            )

        # Prepare batch data
        values = [
            (
                event.run_id,
                event.wallet,
                event.ca,
                event.action,
                event.tx_time,
                event.tx_sig,
                event.amount,
                event.amount_unit,
                event.price,
                event.src_url,
                event.source,
                event.raw_json,
                event.scraped_at,
            )
            for event in events
        ]

        # Batch insert
        conn.executemany(
            """
            INSERT INTO tracker_events (
                run_id, wallet, ca, action, tx_time, tx_sig, amount, amount_unit,
                price, src_url, source, raw_json, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )

        # Get count after insert
        after_count = conn.execute("SELECT COUNT(*) FROM tracker_events").fetchone()[0]

        inserted_count = len(events)
        deduped_count = inserted_count - (after_count - before_count)

        return inserted_count, deduped_count

    def get_tracker_events(self, run_id: Optional[str] = None, limit: int = 100) -> List[dict]:
        """
        Retrieve tracker events.

        Args:
            run_id: Filter by run ID (optional)
            limit: Maximum number of events to return

        Returns:
            List of tracker event records as dicts
        """
        conn = self.connect()

        if run_id:
            result = conn.execute(
                "SELECT * FROM tracker_events WHERE run_id = ? LIMIT ?", [run_id, limit]
            ).fetchall()
        else:
            result = conn.execute("SELECT * FROM tracker_events LIMIT ?", [limit]).fetchall()

        if result:
            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]
        return []

    # ==================== STATISTICS ====================

    def get_stats(self) -> dict:
        """
        Get database statistics.

        Returns:
            Dictionary with counts and stats
        """
        conn = self.connect()

        runs_count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        pulse_count = conn.execute("SELECT COUNT(*) FROM pulse_items").fetchone()[0]
        tracker_count = conn.execute("SELECT COUNT(*) FROM tracker_events").fetchone()[0]

        try:
            tokens_count = conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
            metrics_count = conn.execute("SELECT COUNT(*) FROM token_metrics").fetchone()[0]
        except Exception:
            tokens_count = 0
            metrics_count = 0

        return {
            "runs": runs_count,
            "pulse_items": pulse_count,
            "tracker_events": tracker_count,
            "tokens": tokens_count,
            "token_metrics": metrics_count,
        }

    # ==================== TOKEN ANALYTICS ====================

    def list_tokens(self, chain: str = "sol", limit: int = 100, offset: int = 0) -> List[dict]:
        """
        List tokens with their latest metrics and summaries.

        Args:
            chain: Chain identifier (default: 'sol')
            limit: Maximum number of tokens to return
            offset: Number of tokens to skip

        Returns:
            List of token overview records as dicts
        """
        conn = self.connect()

        result = conn.execute(
            """
            SELECT
                t.ca,
                t.chain,
                t.token_name,
                t.symbol,
                t.first_seen_at,
                t.last_seen_at,
                t.last_pulse_at,
                t.last_tracker_at,
                t.latest_segment,
                t.latest_floor_price,
                tm.score,
                tm.price_usd,
                tm.price_change_1h,
                tm.price_change_6h,
                tm.volume_usd_1h,
                tm.volume_usd_6h,
                tm.volume_usd_24h,
                tm.trade_count_1h,
                tm.trade_count_6h,
                tm.trade_count_24h,
                tm.buy_sell_ratio,
                tm.liquidity_score,
                tm.risk_flags,
                tm.sparkline,
                ts.headline,
                ts.bullet_1,
                ts.bullet_2,
                ts.bullet_3,
                ts.bullet_4,
                ts.bullet_5,
                ts.sentiment
            FROM tokens t
            LEFT JOIN token_metrics tm ON t.ca = tm.ca AND t.chain = tm.chain
            LEFT JOIN token_summaries ts ON t.ca = ts.ca AND t.chain = ts.chain
            WHERE t.chain = ?
            ORDER BY t.last_seen_at DESC
            LIMIT ? OFFSET ?
            """,
            [chain, limit, offset],
        ).fetchall()

        if result:
            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]
        return []

    def get_token(self, ca: str, chain: str = "sol") -> Optional[dict]:
        """
        Get detailed token information by contract address.

        Args:
            ca: Contract address
            chain: Chain identifier (default: 'sol')

        Returns:
            Token overview record as dict or None if not found
        """
        conn = self.connect()

        result = conn.execute(
            """
            SELECT
                t.ca,
                t.chain,
                t.token_name,
                t.symbol,
                t.first_seen_at,
                t.last_seen_at,
                t.last_pulse_at,
                t.last_tracker_at,
                t.latest_segment,
                t.latest_floor_price,
                tm.score,
                tm.price_usd,
                tm.price_change_1h,
                tm.price_change_6h,
                tm.volume_usd_1h,
                tm.volume_usd_6h,
                tm.volume_usd_24h,
                tm.trade_count_1h,
                tm.trade_count_6h,
                tm.trade_count_24h,
                tm.buy_sell_ratio,
                tm.liquidity_score,
                tm.risk_flags,
                tm.sparkline,
                ts.headline,
                ts.bullet_1,
                ts.bullet_2,
                ts.bullet_3,
                ts.bullet_4,
                ts.bullet_5,
                ts.sentiment
            FROM tokens t
            LEFT JOIN token_metrics tm ON t.ca = tm.ca AND t.chain = tm.chain
            LEFT JOIN token_summaries ts ON t.ca = ts.ca AND t.chain = ts.chain
            WHERE t.ca = ? AND t.chain = ?
            """,
            [ca, chain],
        ).fetchone()

        if result:
            columns = [desc[0] for desc in conn.description]
            return dict(zip(columns, result))
        return None

    def get_token_pulse(self, ca: str, chain: str = "sol", limit: int = 100) -> List[dict]:
        """
        Get pulse snapshots for a specific token.

        Args:
            ca: Contract address
            chain: Chain identifier (default: 'sol')
            limit: Maximum number of snapshots to return

        Returns:
            List of pulse snapshot records as dicts
        """
        conn = self.connect()

        result = conn.execute(
            """
            SELECT
                ca,
                ? as chain,
                segment,
                floor_minute,
                floor_price,
                token_name,
                symbol,
                run_id,
                scraped_at
            FROM pulse_items
            WHERE ca = ?
            ORDER BY floor_minute DESC
            LIMIT ?
            """,
            [chain, ca, limit],
        ).fetchall()

        if result:
            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]
        return []

    def get_token_trackers(self, ca: str, chain: str = "sol", limit: int = 100) -> List[dict]:
        """
        Get tracker event summary for a specific token.

        Args:
            ca: Contract address
            chain: Chain identifier (default: 'sol')
            limit: Maximum number of events to return

        Returns:
            Token tracker summary as dict
        """
        conn = self.connect()

        # Get aggregated tracker summary
        summary = conn.execute(
            """
            SELECT
                ca,
                ? as chain,
                COUNT(*) as trade_count,
                COUNT(DISTINCT wallet) as unique_wallets,
                COUNT(*) FILTER (WHERE action = 'buy') as buy_count,
                COUNT(*) FILTER (WHERE action = 'sell') as sell_count,
                SUM(price * amount) as total_volume_usd,
                AVG(price) as avg_price_usd,
                MIN(tx_time) as first_trade_at,
                MAX(tx_time) as last_trade_at
            FROM tracker_events
            WHERE ca = ?
            GROUP BY ca
            """,
            [chain, ca],
        ).fetchone()

        if summary:
            columns = [desc[0] for desc in conn.description]
            result = dict(zip(columns, summary))

            # Get top actions
            top_actions = conn.execute(
                """
                SELECT action, COUNT(*) as count
                FROM tracker_events
                WHERE ca = ?
                GROUP BY action
                ORDER BY count DESC
                LIMIT 5
                """,
                [ca],
            ).fetchall()

            result["top_actions"] = json.dumps(
                [{"action": row[0], "count": row[1]} for row in top_actions]
            )

            return result

        return {
            "ca": ca,
            "chain": chain,
            "trade_count": 0,
            "unique_wallets": 0,
            "buy_count": 0,
            "sell_count": 0,
            "total_volume_usd": None,
            "avg_price_usd": None,
            "first_trade_at": None,
            "last_trade_at": None,
            "top_actions": "[]",
        }

    def get_price_history(self, ca: str, chain: str = "sol", limit: int = 100) -> List[dict]:
        """
        Get price history for a specific token.

        Args:
            ca: Contract address
            chain: Chain identifier (default: 'sol')
            limit: Maximum number of price points to return

        Returns:
            List of price history records as dicts
        """
        conn = self.connect()

        result = conn.execute(
            """
            SELECT
                ca,
                chain,
                segment,
                bucket,
                floor_price,
                run_id,
                scraped_at
            FROM token_price_history
            WHERE ca = ? AND chain = ?
            ORDER BY bucket DESC
            LIMIT ?
            """,
            [ca, chain, limit],
        ).fetchall()

        if result:
            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]
        return []


# Convenience function for context manager usage
def get_database(db_path: str = "data/axiom.duckdb") -> Database:
    """
    Get database instance.

    Args:
        db_path: Path to DuckDB database file

    Returns:
        Database instance
    """
    return Database(db_path)
