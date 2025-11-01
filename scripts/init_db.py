"""
Database initialization script for DuckDB.

Creates tables with unique constraints for deduplication:
- runs: metadata for each scraper run
- pulse_items: Pulse tokens with (ca, segment, floor_minute) uniqueness
- tracker_events: Tracker events with (wallet, ca, action, tx_time) uniqueness
"""

import duckdb
import sys
from pathlib import Path


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
        conn.execute("""
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
        """)
        print("✓ Created 'runs' table")
        
        # Create pulse_items table with unique constraint
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pulse_items (
                id INTEGER PRIMARY KEY,
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
        """)
        print("✓ Created 'pulse_items' table")
        
        # Create indexes for pulse_items
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pulse_ca_minute 
            ON pulse_items (ca, floor_minute);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pulse_segment 
            ON pulse_items (segment);
        """)
        print("✓ Created indexes on 'pulse_items'")
        
        # Create tracker_events table with unique constraint
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tracker_events (
                id INTEGER PRIMARY KEY,
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
        """)
        print("✓ Created 'tracker_events' table")
        
        # Create indexes for tracker_events
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trackers_ca_time 
            ON tracker_events (ca, tx_time);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trackers_wallet 
            ON tracker_events (wallet);
        """)
        print("✓ Created indexes on 'tracker_events'")
        
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
        "--db-path",
        type=str,
        default="data/axiom.duckdb",
        help="Path to DuckDB database file"
    )
    
    args = parser.parse_args()
    init_database(args.db_path)
