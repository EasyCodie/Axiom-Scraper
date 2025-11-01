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

Since Axiom requires Google OAuth login, you need to capture your session once:

```powershell
python scripts/setup_auth.py
```

This will:
1. Open a browser window
2. Navigate to Axiom
3. Wait for you to log in with Google
4. Save your session to `storage_state.json`

**Instructions during setup:**
- Click "Sign in with Google" on Axiom
- Complete Google authentication
- Wait until you see the Axiom dashboard
- Close the browser window

Your session will be saved and reused automatically by the scraper.

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

## Project Structure

```
axiom-scraper/
├── axiom/                  # Main package
│   ├── core/              # Core utilities (config, db, logging, models)
│   ├── parse/             # Data parsers (pulse, trackers)
│   ├── persist/           # Database persistence layer
│   ├── agents/            # Scraper agents
│   └── cli/               # Command-line interface
├── configs/               # Configuration files
│   └── config.yaml        # Main configuration
├── scripts/               # Utility scripts
│   ├── init_db.py        # Database initialization
│   └── setup_auth.py     # Authentication setup
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
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
