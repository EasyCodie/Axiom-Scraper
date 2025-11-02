"""Verification script for user-centric database tables."""

import sys

try:
    import duckdb
except ImportError:
    print("DuckDB not installed. Run: pip install duckdb")
    sys.exit(1)

from scripts.init_db import init_database


def verify_tables():
    """Verify that all user-centric tables were created."""
    db_path = "/tmp/test_user_tables.duckdb"

    print("Initializing database...")
    init_database(db_path)

    print(f"\nConnecting to {db_path}...")
    conn = duckdb.connect(db_path)

    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]

    print(f"\nTotal tables: {len(tables)}")

    expected_user_tables = {
        "user_profiles",
        "favorite_tokens",
        "watchlists",
        "watchlist_tokens",
        "saved_comparisons",
        "comparison_tokens",
        "alerts",
        "alert_channels",
        "alert_events",
    }

    found_user_tables = [t for t in table_names if t in expected_user_tables]

    print(f"\nUser-centric tables found: {len(found_user_tables)}/{len(expected_user_tables)}")
    for name in sorted(found_user_tables):
        print(f"  ✓ {name}")

    missing = expected_user_tables - set(found_user_tables)
    if missing:
        print("\nMissing tables:")
        for name in sorted(missing):
            print(f"  ✗ {name}")
        conn.close()
        sys.exit(1)

    print("\nVerifying table schemas...")

    for table in sorted(found_user_tables):
        result = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
        print(f"\n{table} ({len(result)} columns):")
        for row in result:
            col_name = row[1]
            col_type = row[2]
            print(f"  - {col_name}: {col_type}")

    conn.close()
    print("\n✓ All user-centric tables verified successfully!")


if __name__ == "__main__":
    verify_tables()
