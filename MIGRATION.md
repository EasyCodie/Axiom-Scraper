# Database Migration Guide: User-Centric Tables

This guide explains how to upgrade an existing DuckDB database to include user-centric tables for personalization features.

## What's New

Nine new tables have been added to support user-centric features:

1. **user_profiles** - Store user account information (Supabase UUID)
2. **favorite_tokens** - Track user's favorite tokens
3. **watchlists** - Custom token watchlists
4. **watchlist_tokens** - Tokens within watchlists
5. **saved_comparisons** - Saved token comparisons
6. **comparison_tokens** - Tokens within comparisons
7. **alerts** - Price and event alerts
8. **alert_channels** - Alert delivery channels (email, webhook, etc.)
9. **alert_events** - Alert trigger and delivery history

## Migration Steps

### 1. Backup Your Database

Always backup before running migrations:

```bash
cp data/axiom.duckdb data/axiom.duckdb.backup
```

### 2. Run Database Initializer

The init script uses `CREATE TABLE IF NOT EXISTS`, so existing data is preserved:

```bash
python scripts/init_db.py --db-path data/axiom.duckdb
```

Expected output:
```
Initializing database at: data/axiom.duckdb
✓ Created 'runs' table
...
✓ Created 'user_profiles' table
✓ Created 'favorite_tokens' table
✓ Created indexes on 'favorite_tokens'
✓ Created 'watchlists' table
...
✓ Database initialized successfully with 17 tables
```

### 3. Verify Migration

Check that new tables were created:

```bash
python scripts/verify_user_tables.py
```

Or verify programmatically:

```python
from axiom.core.db import Database

db = Database("data/axiom.duckdb")
with db:
    stats = db.get_stats()
    print(f"Database stats: {stats}")
    
    # Try user operations
    profile = db.get_user_profile("test-user")
    print(f"User profile exists: {profile is not None}")
```

## Data Models

All new models are available in `axiom.core.models`:

- `UserProfile`
- `FavoriteToken`
- `Watchlist`
- `WatchlistToken`
- `SavedComparison`
- `ComparisonToken`
- `Alert`
- `AlertChannel`
- `AlertEvent`

## Database Methods

New CRUD methods in `axiom.core.db.Database`:

### User Profiles
- `upsert_user_profile(profile: UserProfile)`
- `get_user_profile(user_id: str)`
- `delete_user_profile(user_id: str)`

### Favorites
- `add_favorite_token(favorite: FavoriteToken)`
- `remove_favorite_token(user_id: str, ca: str, chain: str)`
- `list_favorite_tokens(user_id: str, chain: str)`

### Watchlists
- `create_watchlist(watchlist: Watchlist)`
- `update_watchlist(watchlist: Watchlist)`
- `delete_watchlist(watchlist_id: str)`
- `get_watchlist(watchlist_id: str)`
- `list_watchlists(user_id: str)`
- `add_watchlist_token(token: WatchlistToken)`
- `remove_watchlist_token(watchlist_id: str, ca: str, chain: str)`
- `list_watchlist_tokens(watchlist_id: str)`

### Comparisons
- `create_comparison(comparison: SavedComparison)`
- `update_comparison(comparison: SavedComparison)`
- `delete_comparison(comparison_id: str)`
- `get_comparison(comparison_id: str)`
- `list_comparisons(user_id: str)`
- `add_comparison_token(token: ComparisonToken)`
- `remove_comparison_token(comparison_id: str, ca: str, chain: str)`
- `list_comparison_tokens(comparison_id: str)`

### Alerts
- `create_alert(alert: Alert)`
- `update_alert(alert: Alert)`
- `delete_alert(alert_id: str)`
- `get_alert(alert_id: str)`
- `list_alerts(user_id: str, is_active: bool, ca: str)`
- `add_alert_channel(channel: AlertChannel)`
- `remove_alert_channel(alert_id: str, channel_type: str)`
- `list_alert_channels(alert_id: str)`
- `log_alert_event(event: AlertEvent)`
- `update_alert_event(event: AlertEvent)`
- `list_alert_events(alert_id: str, limit: int, offset: int)`

## Key Features

### Manual Cascade Deletes
All user data is linked via foreign keys (DuckDB does not support CASCADE constraints). When deleting a user profile, you must manually clean up related data:

```python
with Database("data/axiom.duckdb") as db:
    user_id = "user-uuid"
    
    # Delete user data in order (children first)
    # Delete alerts and related data
    alerts = db.list_alerts(user_id)
    for alert in alerts:
        db.delete_alert(alert["alert_id"])  # Also removes channels and events manually
    
    # Delete comparisons and their tokens
    comparisons = db.list_comparisons(user_id)
    for comp in comparisons:
        db.delete_comparison(comp["comparison_id"])  # Also removes tokens manually
    
    # Delete watchlists and their tokens
    watchlists = db.list_watchlists(user_id)
    for watchlist in watchlists:
        db.delete_watchlist(watchlist["watchlist_id"])  # Also removes tokens manually
    
    # Delete favorites
    favorites = db.list_favorite_tokens(user_id)
    for fav in favorites:
        db.remove_favorite_token(user_id, fav["ca"], fav["chain"])
    
    # Finally delete the user profile
    db.delete_user_profile(user_id)
```

The Database class methods handle child record deletion internally for parent entities (watchlists, comparisons, alerts).

### Unique Constraints
- **favorite_tokens**: `(user_id, ca, chain)` - One favorite per token per user
- **watchlist_tokens**: `(watchlist_id, ca, chain)` - One entry per token per watchlist
- **comparison_tokens**: `(comparison_id, ca, chain)` - Unique token per comparison
- **comparison_tokens**: Separate unique index on `(comparison_id, position)` - Unique positions
- **alert_channels**: `(alert_id, channel_type)` - One channel config per type per alert

### Transactional Integrity
All multi-step operations use transactions to ensure consistency:
- Adding watchlist tokens updates the watchlist's `updated_at` timestamp
- Adding comparison tokens updates the comparison's `updated_at` timestamp
- All upsert operations are atomic

## Testing

Run unit tests to verify functionality:

```bash
pytest tests/unit/db/ -v
```

Tests cover:
- User profile CRUD operations
- Favorite token management
- Watchlist operations with cascade deletes
- Comparison management with position constraints
- Alert lifecycle and delivery tracking
- Foreign key cascade behavior
- Unique constraint enforcement

## Rollback

If you need to revert:

```bash
# Restore from backup
rm data/axiom.duckdb
cp data/axiom.duckdb.backup data/axiom.duckdb
```

Or drop the new tables:

```python
import duckdb

conn = duckdb.connect("data/axiom.duckdb")

tables_to_drop = [
    "alert_events",
    "alert_channels",
    "alerts",
    "comparison_tokens",
    "saved_comparisons",
    "watchlist_tokens",
    "watchlists",
    "favorite_tokens",
    "user_profiles",
]

for table in tables_to_drop:
    conn.execute(f"DROP TABLE IF EXISTS {table}")

conn.close()
```

## Example Usage

See `README.md` for complete examples of:
- Creating user profiles
- Managing favorites
- Building watchlists
- Saving comparisons
- Setting up alerts

## Support

For issues or questions, contact the development team or file a ticket.
