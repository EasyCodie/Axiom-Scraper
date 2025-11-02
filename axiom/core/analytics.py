"""
Analytics module for computing token metrics, scores, and summaries.

Provides functions to aggregate data from pulse_items and tracker_events
into denormalized token_metrics and token_summaries tables.
"""

from datetime import timedelta

import duckdb

from axiom.core.models import eet_now


def rebuild_token_views(
    conn: duckdb.DuckDBPyConnection, chain: str = "sol", bootstrap_metrics: bool = True
) -> dict:
    """Rebuild denormalized token tables from pulse_items and tracker_events."""
    # Clear existing analytics data for the chain
    if bootstrap_metrics:
        conn.execute("DELETE FROM token_metrics WHERE chain = ?", [chain])
        conn.execute("DELETE FROM token_summaries WHERE chain = ?", [chain])
    conn.execute("DELETE FROM token_price_history WHERE chain = ?", [chain])
    conn.execute("DELETE FROM tokens WHERE chain = ?", [chain])

    # Rebuild tokens table
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

    # Rebuild price history from pulse snapshots
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

    if bootstrap_metrics:
        # Initialize metrics and summaries with placeholder rows
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
                '[]'
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

    tokens_count = conn.execute("SELECT COUNT(*) FROM tokens WHERE chain = ?", [chain]).fetchone()[
        0
    ]
    price_rows = conn.execute(
        "SELECT COUNT(*) FROM token_price_history WHERE chain = ?", [chain]
    ).fetchone()[0]

    return {"tokens": tokens_count, "price_history": price_rows}


def compute_token_metrics(
    conn: duckdb.DuckDBPyConnection, chain: str = "sol", lookback_hours: int = 24
) -> int:
    """
    Compute and update token_metrics for all tokens in the specified chain.

    Aggregates data from pulse_items and tracker_events to calculate:
    - Price metrics (current, change %)
    - Volume metrics (1h, 6h, 24h)
    - Trade counts and buy/sell ratios
    - Liquidity score
    - Risk flags
    - Sparkline data
    - Axiom score (composite metric)

    Args:
        conn: DuckDB connection
        chain: Chain identifier (default: 'sol')
        lookback_hours: Hours to look back for metrics (default: 24)

    Returns:
        Number of tokens updated
    """
    now = eet_now()
    cutoff_1h = now - timedelta(hours=1)
    cutoff_6h = now - timedelta(hours=6)
    cutoff_24h = now - timedelta(hours=lookback_hours)

    # Compute price metrics from pulse data
    conn.execute(
        """
        WITH current_prices AS (
            SELECT
                ca,
                max_by(floor_price, floor_minute) AS price_current,
                max_by(floor_minute, floor_minute) AS price_time
            FROM pulse_items
            WHERE scraped_at >= ?
            GROUP BY ca
        ),
        historical_prices AS (
            SELECT
                ca,
                max_by(floor_price, floor_minute) FILTER (WHERE floor_minute <= ?) AS price_1h_ago,
                max_by(floor_price, floor_minute) FILTER (WHERE floor_minute <= ?) AS price_6h_ago
            FROM pulse_items
            WHERE scraped_at >= ?
            GROUP BY ca
        )
        UPDATE token_metrics
        SET
            price_usd = cp.price_current,
            price_change_1h = CASE
                WHEN hp.price_1h_ago > 0 AND cp.price_current IS NOT NULL
                THEN ((cp.price_current - hp.price_1h_ago) / hp.price_1h_ago) * 100.0
                ELSE NULL
            END,
            price_change_6h = CASE
                WHEN hp.price_6h_ago > 0 AND cp.price_current IS NOT NULL
                THEN ((cp.price_current - hp.price_6h_ago) / hp.price_6h_ago) * 100.0
                ELSE NULL
            END,
            as_of = ?
        FROM current_prices cp
        LEFT JOIN historical_prices hp ON cp.ca = hp.ca
        WHERE token_metrics.ca = cp.ca AND token_metrics.chain = ?;
        """,
        [cutoff_24h, cutoff_1h, cutoff_6h, cutoff_24h, now, chain],
    )

    # Compute volume and trade count from tracker_events
    conn.execute(
        """
        WITH tracker_stats AS (
            SELECT
                ca,
                COUNT(*) FILTER (WHERE tx_time >= ?) AS trade_count_1h,
                COUNT(*) FILTER (WHERE tx_time >= ?) AS trade_count_6h,
                COUNT(*) FILTER (WHERE tx_time >= ?) AS trade_count_24h,
                SUM(price * amount) FILTER (WHERE tx_time >= ? AND price IS NOT NULL AND amount IS NOT NULL) AS volume_1h,
                SUM(price * amount) FILTER (WHERE tx_time >= ? AND price IS NOT NULL AND amount IS NOT NULL) AS volume_6h,
                SUM(price * amount) FILTER (WHERE tx_time >= ? AND price IS NOT NULL AND amount IS NOT NULL) AS volume_24h,
                COUNT(*) FILTER (WHERE tx_time >= ? AND action = 'buy') AS buy_count_1h,
                COUNT(*) FILTER (WHERE tx_time >= ? AND action = 'sell') AS sell_count_1h
            FROM tracker_events
            WHERE scraped_at >= ?
            GROUP BY ca
        )
        UPDATE token_metrics
        SET
            trade_count_1h = ts.trade_count_1h,
            trade_count_6h = ts.trade_count_6h,
            trade_count_24h = ts.trade_count_24h,
            volume_usd_1h = ts.volume_1h,
            volume_usd_6h = ts.volume_6h,
            volume_usd_24h = ts.volume_24h,
            buy_sell_ratio = CASE
                WHEN ts.sell_count_1h > 0 THEN ts.buy_count_1h::DOUBLE / ts.sell_count_1h
                WHEN ts.buy_count_1h > 0 THEN 999.0
                ELSE 1.0
            END,
            as_of = ?
        FROM tracker_stats ts
        WHERE token_metrics.ca = ts.ca AND token_metrics.chain = ?;
        """,
        [
            cutoff_1h,
            cutoff_6h,
            cutoff_24h,
            cutoff_1h,
            cutoff_6h,
            cutoff_24h,
            cutoff_1h,
            cutoff_1h,
            cutoff_24h,
            now,
            chain,
        ],
    )

    # Compute sparkline data (last 24 hours, 30-minute buckets)
    conn.execute(
        """
        WITH binned AS (
            SELECT
                ca,
                time_bucket(INTERVAL '30 minutes', floor_minute) AS bucket,
                AVG(floor_price) AS avg_price
            FROM pulse_items
            WHERE floor_minute >= ? AND floor_price IS NOT NULL
            GROUP BY ca, bucket
        ),
        sparkline AS (
            SELECT
                ca,
                LIST(avg_price ORDER BY bucket) AS prices
            FROM binned
            GROUP BY ca
        )
        UPDATE token_metrics
        SET sparkline = COALESCE(
            (
                SELECT CAST(prices AS VARCHAR)
                FROM sparkline
                WHERE sparkline.ca = token_metrics.ca
            ),
            '[]'
        )
        WHERE chain = ?;
        """,
        [cutoff_24h, chain],
    )

    # Compute risk flags based on heuristics
    conn.execute(
        """
        UPDATE token_metrics
        SET
            risk_flags = CASE
                WHEN price_change_1h < -50 THEN '["extreme_dump"]'
                WHEN price_change_1h > 200 THEN '["extreme_pump"]'
                WHEN trade_count_1h < 2 THEN '["low_activity"]'
                WHEN buy_sell_ratio > 10 THEN '["extreme_buy_pressure"]'
                WHEN buy_sell_ratio < 0.1 THEN '["extreme_sell_pressure"]'
                ELSE '[]'
            END
        WHERE chain = ?;
        """,
        [chain],
    )

    # Compute composite Axiom score (0-100)
    # Factors: volume, trade count, price momentum, buy/sell ratio
    conn.execute(
        """
        WITH score_components AS (
            SELECT
                ca,
                COALESCE(LEAST(volume_usd_24h / 10000.0, 1.0), 0.0) * 30 AS volume_score,
                COALESCE(LEAST(trade_count_24h / 100.0, 1.0), 0.0) * 25 AS activity_score,
                CASE
                    WHEN price_change_6h > 20 THEN 25
                    WHEN price_change_6h > 0 THEN 15
                    WHEN price_change_6h > -10 THEN 5
                    ELSE 0
                END AS momentum_score,
                CASE
                    WHEN buy_sell_ratio > 2.0 THEN 20
                    WHEN buy_sell_ratio > 1.0 THEN 10
                    WHEN buy_sell_ratio > 0.5 THEN 5
                    ELSE 0
                END AS sentiment_score
            FROM token_metrics
            WHERE chain = ?
        )
        UPDATE token_metrics
        SET score = LEAST(
            sc.volume_score + sc.activity_score + sc.momentum_score + sc.sentiment_score,
            100.0
        )
        FROM score_components sc
        WHERE token_metrics.ca = sc.ca AND token_metrics.chain = ?;
        """,
        [chain, chain],
    )

    updated_count = conn.execute(
        "SELECT COUNT(*) FROM token_metrics WHERE chain = ? AND as_of = ?", [chain, now]
    ).fetchone()[0]

    return updated_count


def compute_token_summaries(conn: duckdb.DuckDBPyConnection, chain: str = "sol") -> int:
    """
    Compute and update token_summaries with five-bullet summaries.

    Generates concise bullet points summarizing token activity:
    - Current price and momentum
    - Volume and trade activity
    - Buy/sell pressure
    - Risk indicators
    - Overall sentiment

    Args:
        conn: DuckDB connection
        chain: Chain identifier (default: 'sol')

    Returns:
        Number of summaries updated
    """
    now = eet_now()

    # Generate bullet points based on metrics
    conn.execute(
        """
        WITH bullet_data AS (
            SELECT
                tm.ca,
                t.token_name,
                t.symbol,
                tm.price_usd,
                tm.price_change_1h,
                tm.price_change_6h,
                tm.volume_usd_24h,
                tm.trade_count_24h,
                tm.buy_sell_ratio,
                tm.risk_flags,
                tm.score
            FROM token_metrics tm
            JOIN tokens t ON tm.ca = t.ca AND tm.chain = t.chain
            WHERE tm.chain = ?
        )
        UPDATE token_summaries
        SET
            headline = COALESCE(
                (SELECT token_name || ' (' || symbol || ')' FROM bullet_data WHERE bullet_data.ca = token_summaries.ca),
                'Token ' || SUBSTR(token_summaries.ca, 1, 8)
            ),
            bullet_1 = COALESCE((
                SELECT 'Price: $' || ROUND(price_usd, 6) ||
                       CASE
                           WHEN price_change_6h > 0 THEN ' (+' || ROUND(price_change_6h, 1) || '% 6h)'
                           WHEN price_change_6h < 0 THEN ' (' || ROUND(price_change_6h, 1) || '% 6h)'
                           ELSE ''
                       END
                FROM bullet_data WHERE bullet_data.ca = token_summaries.ca AND price_usd IS NOT NULL
            ), 'Price data unavailable'),
            bullet_2 = COALESCE((
                SELECT '24h Volume: $' || ROUND(volume_usd_24h, 0) || ' across ' || trade_count_24h || ' trades'
                FROM bullet_data WHERE bullet_data.ca = token_summaries.ca AND volume_usd_24h IS NOT NULL
            ), 'Volume data unavailable'),
            bullet_3 = COALESCE((
                SELECT 'Buy/Sell Ratio: ' || ROUND(buy_sell_ratio, 2) ||
                       CASE
                           WHEN buy_sell_ratio > 2 THEN ' (strong buy pressure)'
                           WHEN buy_sell_ratio > 1 THEN ' (moderate buy pressure)'
                           WHEN buy_sell_ratio < 0.5 THEN ' (strong sell pressure)'
                           ELSE ' (balanced)'
                       END
                FROM bullet_data WHERE bullet_data.ca = token_summaries.ca AND buy_sell_ratio IS NOT NULL
            ), 'Trading data unavailable'),
            bullet_4 = COALESCE((
                SELECT 'Risk Flags: ' ||
                       CASE
                           WHEN risk_flags = '[]' THEN 'None detected'
                           ELSE risk_flags
                       END
                FROM bullet_data WHERE bullet_data.ca = token_summaries.ca
            ), 'Risk assessment unavailable'),
            bullet_5 = COALESCE((
                SELECT 'Axiom Score: ' || ROUND(score, 0) || '/100 ' ||
                       CASE
                           WHEN score >= 75 THEN '(Excellent)'
                           WHEN score >= 50 THEN '(Good)'
                           WHEN score >= 25 THEN '(Fair)'
                           ELSE '(Poor)'
                       END
                FROM bullet_data WHERE bullet_data.ca = token_summaries.ca AND score IS NOT NULL
            ), 'Score unavailable'),
            sentiment = COALESCE((
                SELECT CASE
                    WHEN score >= 60 AND price_change_6h > 10 AND buy_sell_ratio > 1.5 THEN 'bullish'
                    WHEN score >= 40 AND price_change_6h > 0 THEN 'positive'
                    WHEN score < 30 OR price_change_6h < -20 OR buy_sell_ratio < 0.5 THEN 'bearish'
                    ELSE 'neutral'
                END
                FROM bullet_data WHERE bullet_data.ca = token_summaries.ca
            ), 'neutral'),
            as_of = ?
        WHERE chain = ?;
        """,
        [chain, now, chain],
    )

    updated_count = conn.execute(
        "SELECT COUNT(*) FROM token_summaries WHERE chain = ? AND as_of = ?",
        [chain, now],
    ).fetchone()[0]

    return updated_count


def refresh_analytics(conn: duckdb.DuckDBPyConnection, chain: str = "sol") -> dict:
    """
    Refresh all analytics tables for the specified chain.

    This is the main entry point for computing/updating:
    - tokens and token_price_history (denormalized views)
    - token_metrics
    - token_summaries

    Args:
        conn: DuckDB connection
        chain: Chain identifier (default: 'sol')

    Returns:
        Dictionary with update counts
    """
    rebuilt = rebuild_token_views(conn, chain=chain, bootstrap_metrics=True)
    metrics_updated = compute_token_metrics(conn, chain=chain)
    summaries_updated = compute_token_summaries(conn, chain=chain)

    return {
        "chain": chain,
        "tokens_rebuilt": rebuilt["tokens"],
        "price_history_rows": rebuilt["price_history"],
        "metrics_updated": metrics_updated,
        "summaries_updated": summaries_updated,
        "timestamp": eet_now().isoformat(),
    }
