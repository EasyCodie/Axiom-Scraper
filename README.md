# Axiom Meme-Coin Scoring Agent

Phase 1 MVP: Playwright-based data scraper for Axiom trading platform (Solana chain).

## Features

- **Pulse Scraper**: Extracts token snapshot data (price, volume, liquidity)
- **Trackers Scraper**: Captures wallet activity events (trades, transactions)
- **DuckDB Storage**: High-performance analytics database with deduplication
- **EET Timezone**: All timestamps normalized to Eastern European Time (UTC+2)
- **USD Pricing**: Normalized currency in USD
- **Configurable Limits**: Default 20 rows (Pulse), 100 events (Trackers)

## Prerequisites

- Python 3.10 or higher
- Windows 10/11 (PowerShell)

## Quick Start

### 1. Install Dependencies

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

```powershell
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional - defaults are configured)
```

### 3. Initialize Database

```powershell
python scripts/init_db.py
```

Expected output:
```
✓ Created 'runs' table
✓ Created 'pulse_items' table
✓ Created indexes on 'pulse_items'
✓ Created 'tracker_events' table
✓ Created indexes on 'tracker_events'
✓ Database ready at: data/axiom.duckdb
```

### 4. Setup Authentication

Since Axiom requires authentication, capture your session once. By default the script launches a persistent browser profile (more reliable for Google OAuth) using Chrome:

```powershell
python scripts/setup_auth.py
```

Edge option (recommended on Windows if Google flags the browser):

```powershell
python scripts/setup_auth.py --browser-channel msedge
```

This will:
1. Open a browser window (persistent profile at `.user-data/axiom`)
2. Navigate to Axiom
3. Let you log in (Google OAuth or email/password)
4. Save your session to `storage_state.json`

**Instructions during setup:**
- Click "Sign in with Google" on Axiom (or use email/password if preferred)
- Complete authentication
- Wait until you see the Axiom dashboard
- Close the browser window

Your session will be saved and reused automatically by the scraper.

**Auth script options:**
- `--browser-channel` Choose browser channel (default: `chrome`; use `msedge` on Windows)
- `--no-persistent` Opt-out of persistent profile (default is persistent)
- `--user-data-dir` Directory for the persistent profile (default: `.user-data/axiom`)
- `--no-prompt` Skip interactive prompts
- `--verify` Verify existing session headlessly

**Verify authentication:**
```powershell
python scripts/setup_auth.py --verify
```

### 5. Run the Scraper

```powershell
# Scrape Pulse data only
python -m axiom.cli.run_scrape --mode=pulse

# Scrape Trackers data only
python -m axiom.cli.run_scrape --mode=trackers

# Scrape both (default)
python -m axiom.cli.run_scrape --mode=all
```

**CLI Options:**
```
--mode              pulse | trackers | all (default: all)
--max-rows          Max Pulse items to scrape (default: 20)
--max-events        Max Tracker events to scrape (default: 100)
--rate-limit        Concurrent requests limit (default: 5)
--config            Path to config.yaml (default: configs/config.yaml)
--storage-state     Path to auth session (default: storage_state.json)
--headful           Run browser in visible mode (default: headless)
```

## Analytics Layer

The analytics layer aggregates raw scraper data into actionable token metrics and summaries:

### Token Tables

- **`tokens`**: Denormalized view combining pulse and tracker data per token
- **`token_metrics`**: Aggregated metrics (price, volume, trades, scores)
- **`token_summaries`**: Five-bullet human-readable summaries
- **`token_price_history`**: Time-series price data from pulse snapshots

### Axiom Score

The **Axiom Score** (0-100) is a composite metric derived from:

1. **Volume Score** (30 points): 24h trading volume (normalized to $10k cap)
2. **Activity Score** (25 points): Number of trades in 24h (normalized to 100 trades)
3. **Momentum Score** (25 points): 6h price change (positive momentum scores higher)
4. **Sentiment Score** (20 points): Buy/sell ratio (strong buy pressure scores higher)

Risk flags include: `extreme_pump`, `extreme_dump`, `low_activity`, `extreme_buy_pressure`, `extreme_sell_pressure`.

### Five-Bullet Summary

Each token receives an auto-generated summary with 5 concise bullet points:

1. **Price & Momentum**: Current price with 6h change percentage
2. **Volume & Activity**: 24h volume and trade count
3. **Buy/Sell Pressure**: Ratio with qualitative interpretation
4. **Risk Flags**: Detected anomalies or "None detected"
5. **Axiom Score**: Final score with rating (Excellent/Good/Fair/Poor)

### Running Analytics

```powershell
# Compute and update analytics for all tokens
python -m axiom.cli.analytics --chain=sol

# Output results as JSON
python -m axiom.cli.analytics --chain=sol --json
```

The CLI will:
- Rebuild denormalized token views from `pulse_items` and `tracker_events`
- Compute price, volume, and trade metrics
- Calculate Axiom scores
- Generate five-bullet summaries
- Display top tokens by score

### Database Helpers

Use the `Database` class to query analytics:

```python
from axiom.core.db import Database

with Database("data/axiom.duckdb") as db:
    # List all tokens with metrics
    tokens = db.list_tokens(chain="sol", limit=10)
    
    # Get detailed token overview
    token = db.get_token("contract_address", chain="sol")
    
    # Get pulse snapshots
    pulse = db.get_token_pulse("contract_address", limit=50)
    
    # Get tracker event summary
    trackers = db.get_token_trackers("contract_address")
    
    # Get price history
    history = db.get_price_history("contract_address")
```

## Project Structure

```
axiom-scraper/
├── axiom/                  # Main package
│   ├── core/              # Core utilities (config, db, logging, models, analytics)
│   ├── parse/             # Data parsers (pulse, trackers)
│   ├── persist/           # Database persistence layer
│   ├── agents/            # Scraper agents
│   └── cli/               # Command-line interface
├── configs/               # Configuration files
│   └── config.yaml        # Main configuration
├── scripts/               # Utility scripts
│   ├── init_db.py        # Database initialization (includes analytics tables)
│   └── setup_auth.py     # Authentication setup
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   │   └── analytics/    # Analytics tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
├── data/                  # Database and reports (gitignored)
├── logs/                  # Log files (gitignored)
└── docs/                  # Documentation

```

## Development Status

**Current Milestone:** M0 - Repository Scaffolding ✓

**Upcoming Milestones:**
- M1: Core models, config, database persistence
- M2: Playwright utilities, network intercept
- M3: Pulse scraper implementation
- M4: Trackers scraper implementation
- M5: Validation, observability, documentation

## Configuration

Default settings in `configs/config.yaml`:
- **Timezone**: Europe/Athens (EET, UTC+2)
- **Currency**: USD
- **Max Pulse Rows**: 20
- **Max Tracker Events**: 100
- **Database**: DuckDB at `data/axiom.duckdb`

## Troubleshooting

**Authentication expired:**
```powershell
python scripts/setup_auth.py
```

**Database locked or corrupted:**
```powershell
# Reinitialize (WARNING: deletes all data)
rm data/axiom.duckdb
python scripts/init_db.py
```

**Playwright not installed:**
```powershell
playwright install chromium
```

## Testing

```powershell
# Run unit tests
pytest tests/unit/

# Run integration tests (requires ONLINE_TESTS=true in .env)
pytest tests/integration/

# Run all tests with coverage
pytest --cov=axiom tests/
```

## Lint and Format

```powershell
# Format code
black axiom/ tests/

# Lint
ruff axiom/ tests/

# Both
black axiom/ tests/ && ruff axiom/ tests/
```

## License

Internal project - proprietary.

## Support

For issues or questions, contact the development team.
