# AGENTS.md  
*Project : “Axiom Meme-Coin Scoring Agent”*  
*MVP Phase 1: Scraper for Pulse & Trackers data from Axiom*  

## 1. Purpose  
This document provides guidance to automated coding agents (and humans) working on the project.  
It codifies how to fetch, process, score, and report data from the Axiom Trade platform (chain = SOL) for meme-coin investment potential.  
The goal: build tests, maintainability, clarity, and reproducible workflows.

## 2. Scope of This Phase  
- Build a scraper (using Playwright) that navigates to Axiom’s **Pulse** and **Trackers** sections for Solana chain.  
- Extract structured JSON/DOM data for tokens (Pulse) and wallet events (Trackers).  
- Normalize and persist data (SQLite or DuckDB) into defined tables.  
- Provide logs, error handling, deduplication, and a CLI entrypoint.  
- No scoring logic or LLM summarization yet — focus is data ingestion.

## 3. Technology Stack & Agent Expectations  
- **Language**: Python 3.10+ (preferred)  
- **Libraries**: `playwright`, `pydantic`, `sqlite3`/`duckdb`, `tenacity`, `python-dotenv`, `logging`  
- **Structure**: Modular codebase; separation of concerns (scraper vs parser vs storage).  
- **Tests**: Unit tests for parser logic (JSON → models) and integration tests for scraping small sample.  
- **Agent behaviour**:  
  - Use network interception (JSON endpoints) where possible.  
  - Provide fallback for DOM scraping via stable selectors.  
  - Rate-limit and respect ToS (throttling, delay).  
  - Clean error handling and logging.  
  - All code must include docstrings and adhere to style guidelines.

## 4. Project Structure  
/mvp_scraper/
├── scrape/
│ ├── pulse_scraper.py
│ └── tracker_scraper.py
├── models/
│ └── schema.py # Pydantic models for PulseItem, TrackerEvent
├── storage/
│ └── db.py # DB connection, tables definitions
├── utils/
│ └── logging_config.py
├── config.yaml # scraper configuration (caps, delay, chain)
├── run_scrape.py # CLI entrypoint: python run_scrape.py --all
├── tests/
│ ├── test_schema.py
│ ├── test_pulse_parser.py
│ └── test_tracker_parser.py
└── .env # credentials/session state for Playwright

## 5. Coding Conventions  
- Use **snake_case** for functions and variables.  
- Use **PascalCase** for Pydantic models and class definitions.  
- Strict typing and docstrings required for all public methods.  
- Logging: use `logging.getLogger(__name__)` and structured logs (JSON if possible) with `run_id`, `phase`, `item_count`, `errors`.  
- Constants (like URLs, chain identifiers) in `config.yaml` or `constants.py`, not hard-coded.  
- Avoid global mutable state; use dependency injection where possible for testability.

## 6. Scraper Behaviour & Rules  
- **Session setup**: Use Playwright persistent context for login; store `storage_state.json`.  
- **Rate limiting**: Default delay between navigation/actions = **2 seconds**, configurable in `config.yaml`.  
- **Retries**: For network errors or timeouts use exponential back-off (via `tenacity`).  
- **Data capture**:  
  - **Pulse:** Navigate to `https://axiom.trade/pulse?chain=sol`, await network idle, scroll until no further new rows (or item cap).  
  - **Trackers:** Navigate to `https://axiom.trade/trackers?chain=sol`, capture wallet event streams.  
- **Parsing priority**:  
  1. JSON response capture (search for relevant endpoints).  
  2. If JSON unavailable, fallback to DOM parsing (with stable selectors).  
- **Persistence**: Insert into `pulse_snapshot` and `tracker_events` tables with timestamp `captured_at`.  
- **Deduplication**: Prevent duplicate rows by key (e.g., `ca + segment + floor_minute` for Pulse; `wallet + ca + action + tx_time` for Trackers).  
- **Logging & metrics**: Log number of items extracted, run_id, duration, and any errors.

## 7. Configuration  
Store configuration parameters in `config.yaml`, for example:
```yaml
chain: sol
pulse:
  max_rows: 500
  scroll_timeout: 20    # seconds
  delay_between_scrolls: 1
tracker:
  max_events: 1000
  wallet_sample: 100
rate_limit:
  delay_sec: 2
db:
  file: "data/mvp.db"
```

## 8. User Data Tables  
- User personalization features are stored in DuckDB via `user_profiles`, `favorite_tokens`, `watchlists`, `watchlist_tokens`, `saved_comparisons`, `comparison_tokens`, `alerts`, `alert_channels`, and `alert_events`.  
- All tables reference `user_profiles.user_id` (Supabase UUID); DuckDB lacks cascade constraints, so the `Database` helpers manually clean up child rows.  
- CRUD helpers live in `axiom.core.db.Database`; prefer the typed Pydantic models in `axiom.core.models` for inserts/updates.  
- To add these tables to an existing DuckDB file, rerun the initializer with the same path (no data loss):  
  ```bash
  python scripts/init_db.py --db-path data/axiom.duckdb
  ```
- Seeded data is unaffected; tables use `CREATE TABLE IF NOT EXISTS` and maintain existing content