"""
CLI command for running token analytics aggregations.

Usage:
    python -m axiom.cli.analytics --chain=sol
    python -m axiom.cli.analytics --refresh
"""

import argparse
import json
import sys
from pathlib import Path

from axiom.core.analytics import refresh_analytics
from axiom.core.db import Database


def main():
    parser = argparse.ArgumentParser(description="Compute and update token analytics metrics")
    parser.add_argument(
        "--chain",
        type=str,
        default="sol",
        help="Chain identifier (default: sol)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/axiom.duckdb",
        help="Path to DuckDB database file",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh all analytics tables",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    # Validate database exists
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"Error: Database not found at {args.db_path}", file=sys.stderr)
        print("Run 'python scripts/init_db.py' to initialize the database.", file=sys.stderr)
        sys.exit(1)

    # Connect to database
    db = Database(args.db_path)

    try:
        with db:
            conn = db.connect()

            # Check if analytics tables exist
            tables = conn.execute("SHOW TABLES;").fetchall()
            table_names = [t[0] for t in tables]

            required_tables = ["tokens", "token_metrics", "token_summaries"]
            missing_tables = [t for t in required_tables if t not in table_names]

            if missing_tables:
                print(
                    f"Error: Missing analytics tables: {', '.join(missing_tables)}", file=sys.stderr
                )
                print(
                    "Run 'python scripts/init_db.py' to create analytics tables.", file=sys.stderr
                )
                sys.exit(1)

            # Refresh analytics
            if not args.json:
                print(f"Computing analytics for chain '{args.chain}'...")

            result = refresh_analytics(conn, chain=args.chain)

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"✓ Analytics updated for chain '{result['chain']}':")
                print(f"  - Token metrics updated: {result['metrics_updated']}")
                print(f"  - Token summaries updated: {result['summaries_updated']}")
                print(f"  - Timestamp: {result['timestamp']}")

                # Show sample of top tokens
                tokens = db.list_tokens(chain=args.chain, limit=5)
                if tokens:
                    print("\nTop 5 tokens by score:")
                    sorted_tokens = sorted(tokens, key=lambda t: t.get("score") or 0, reverse=True)
                    for idx, token in enumerate(sorted_tokens[:5], 1):
                        name = token.get("token_name") or token.get("symbol") or token["ca"][:8]
                        score = token.get("score")
                        if score is not None:
                            print(f"  {idx}. {name}: {score:.1f}/100")
                        else:
                            print(f"  {idx}. {name}: No score")

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
