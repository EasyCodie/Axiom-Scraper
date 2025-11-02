# Product Requirements Document (PRD)
## Project: Axiom Meme-Coin Scoring Agent (Phase 1 MVP)

---

### 1. Overview
The Axiom Meme-Coin Scoring Agent is an AI-powered data intelligence system designed to extract, structure, and analyze trader and token data from the **Axiom** trading platform.  
The MVP (Phase 1) focuses exclusively on **data ingestion**—building a robust Playwright-based scraper that collects data from **Pulse** and **Trackers** sections for the **Solana** chain, stores it locally, and prepares it for downstream analysis and scoring.

---

### 2. Objectives
- Automate the collection of on-chain meme coin data from Axiom’s **Pulse** and **Trackers** dashboards.  
- Normalize and store token and trader data for further analysis.  
- Establish a structured, testable foundation for Phase 2 (AI scoring and LLM summarization).  
- Ensure scalability, maintainability, and data reliability from the first iteration.

---

### 3. Success Metrics
| Category | KPI | Target |
|-----------|-----|--------|
| **Data Accuracy** | Correctly parsed tokens/events vs. raw data | ≥95% accuracy |
| **Stability** | Successful runs without failure | ≥90% across 50+ runs |
| **Performance** | Data extraction time per run | <90 seconds per full scrape |
| **Data Volume** | Tokens and wallet events stored per run | ≥500 tokens, ≥1,000 tracker events |
| **Maintainability** | Code coverage & lint compliance | ≥85% unit test pass rate |

---

### 4. Scope

#### In Scope (Phase 1)
- Playwright scraper for:
  - `https://axiom.trade/pulse?chain=sol`
  - `https://axiom.trade/trackers?chain=sol`
- Capture **token**, **wallet**, and **activity** data:
  - Token name, contract address, price, % changes, volume, liquidity, and age.
  - Wallet address, label, token traded, action (buy/sell), timestamp, and PnL.
- Network interception of JSON payloads and DOM fallback.
- Data normalization with Pydantic models (`PulseItem`, `TrackerEvent`).
- Local storage via SQLite or DuckDB.
- CLI runner for manual and scheduled scrapes.
- Analytics layer (`tokens`, `token_metrics`, `token_summaries`, `token_price_history`) with automated scoring and summaries.
- Logging, error handling, and deduplication.

#### Out of Scope (Phase 1)
- LLM-based (GPT/Claude) summarization and report generation.
- UI/dashboard components.
- Multi-chain expansion beyond Solana.
- Automated trading signals.

---

### 5. Functional Requirements

#### 5.1 Pulse Scraper
- Navigate to Pulse dashboard.
- Wait until `networkidle`.
- Capture token feed via JSON endpoints.
- If unavailable, scrape visible DOM elements.
- Normalize and store in `pulse_snapshot` table with timestamp.

#### 5.2 Trackers Scraper
- Navigate to Trackers dashboard.
- Capture wallet activity feed.
- Extract last known trades and wallet statistics.
- Store in `tracker_events` table with timestamp.

#### 5.3 Data Processing
- Deduplicate based on (`ca`, `segment`, `captured_at_floor_minute`) for Pulse.
- Deduplicate based on (`wallet`, `ca`, `action`, `tx_time`) for Trackers.
- Validate all entries via Pydantic models.
- Record execution metadata in `runs` table.

#### 5.4 CLI
- Commands:
  - `python run_scrape.py --mode=pulse`
  - `python run_scrape.py --mode=trackers`
  - `python run_scrape.py --all`
- Configurable caps: `max_rows`, `max_events`, `rate_limit`.

#### 5.5 Analytics Layer
- Rebuild denormalized tables/views (`tokens`, `token_metrics`, `token_summaries`, `token_price_history`).
- Compute token-level metrics: price momentum, volume deltas, trade counts, liquidity proxy, buy/sell ratios.
- Calculate Axiom composite score (0–100) and generate risk flags.
- Produce five-bullet token summaries per refresh.
- Expose CLI: `python -m axiom.cli.analytics --chain=sol` with JSON output option.
- Provide database helpers for API layer (`list_tokens`, `get_token`, `get_token_pulse`, `get_token_trackers`, `get_price_history`).

---

### 6. Non-Functional Requirements

| Category | Requirement |
|-----------|-------------|
| **Reliability** | Graceful recovery via retries and exponential backoff |
| **Performance** | Async execution for network-bound tasks |
| **Maintainability** | Modular architecture and docstrings for all functions |
| **Security** | Environment-based secrets; cookies stored securely |
| **Compliance** | Respect site ToS; include scraping disclaimer |
| **Scalability** | Design modularly for multi-chain future support |

---

### 7. Data Model

#### Table: `pulse_snapshot`
| Column | Type | Description |
|---------|------|-------------|
| id | INTEGER (PK) | Unique record ID |
| captured_at | TIMESTAMP | Time of extraction |
| segment | TEXT | Category (new, surging, migrated) |
| token | TEXT | Token name |
| ca | TEXT | Contract address |
| price | FLOAT | Current price |
| chg_1h / chg_4h | FLOAT | Price change over time |
| vol_1h / vol_4h | FLOAT | Volume metrics |
| liq / mcap | FLOAT | Liquidity / Market cap |
| age_s | INT | Token age in seconds |
| raw_json | TEXT | Full response payload |

#### Table: `tracker_events`
| Column | Type | Description |
|---------|------|-------------|
| id | INTEGER (PK) | Unique record ID |
| captured_at | TIMESTAMP | Time of extraction |
| wallet | TEXT | Wallet address |
| label | TEXT | Wallet tag if known |
| action | TEXT | buy / sell |
| ca | TEXT | Contract address |
| token | TEXT | Token symbol |
| qty | FLOAT | Quantity traded |
| usd_value | FLOAT | USD value |
| pnl | FLOAT | Profit/loss data |
| tx_time | TIMESTAMP | Time of transaction |
| raw_json | TEXT | Full response payload |

#### Table: `runs`
| Column | Type | Description |
|---------|------|-------------|
| id | INTEGER (PK) | Run ID |
| started_at | TIMESTAMP | Start time |
| finished_at | TIMESTAMP | End time |
| ok | BOOLEAN | Success status |
| notes | TEXT | Run details or errors |

---
## 8. Architecture Overview

The MVP is structured as a modular data-ingestion pipeline built around two core scrapers — **Pulse** and **Trackers** — both orchestrated through a unified CLI entrypoint.  
Each scraper operates independently, capturing live data from Axiom, parsing it into standardized models, and storing it in a local database.

### System Flow

               ┌────────────────────────────┐
               │        CLI Layer            │
               │      (run_scrape.py)        │
               └─────────────┬───────────────┘
                             │
                             ▼
    ┌──────────────────────────────────────────────────┐
    │                Scraper Layer                     │
    │  ┌──────────────────────┐   ┌────────────────────┐│
    │  │   Pulse Scraper      │   │  Trackers Scraper  ││
    │  │ (Playwright + JSON)  │   │ (Playwright + JSON)││
    │  └───────────┬──────────┘   └──────────┬─────────┘│
    └───────────────┼────────────────────────┼───────────┘
                    │                        │
                    ▼                        ▼
    ┌────────────────────┐        ┌─────────────────────┐
    │  Data Parser Layer  │        │  Data Parser Layer  │
    │ (Pydantic Models)   │        │ (Pydantic Models)   │
    └──────────┬──────────┘        └──────────┬──────────┘
               │                             │
               ▼                             ▼
    ┌────────────────────┐        ┌─────────────────────┐
    │   Storage Layer     │        │   Storage Layer     │
    │ (SQLite / DuckDB)   │        │ (SQLite / DuckDB)   │
    └──────────┬──────────┘        └──────────┬──────────┘
               │                             │
               ▼                             ▼
          ┌─────────────────────────────────────────────┐
          │            Logging & Validation              │
          │ (Dedupe, Schema Checks, Run Metadata)        │
          └─────────────────────────────────────────────┘

### Layer Descriptions

- **CLI Layer (`run_scrape.py`)**  
  - Main entrypoint for running either or both scrapers.  
  - Accepts flags: `--mode=pulse`, `--mode=trackers`, or `--all`.  
  - Handles config loading, scheduling, and logging.

- **Scraper Layer**  
  - Uses **Playwright** for session-based navigation.  
  - Captures data through JSON network intercepts, with DOM parsing as fallback.  
  - Respects rate limits and includes automatic retries for stability.

- **Data Parser Layer**  
  - Cleans and validates raw data using **Pydantic** models (`PulseItem`, `TrackerEvent`).  
  - Ensures consistent typing, timestamp normalization, and deduplication keys.

- **Storage Layer**  
  - Writes parsed and validated records to **SQLite/DuckDB**.  
  - Includes schema for `pulse_snapshot`, `tracker_events`, and `runs` tables.  
  - Supports both local caching and future remote migration.

- **Logging & Validation Layer**  
  - Maintains structured logs per run (with `run_id`, errors, and item counts).  
  - Performs post-run validation and deduplication.  
  - Enables downstream consumption by scoring and LLM modules (Phase 2+).

This modular architecture ensures that each component can evolve independently — e.g., replacing scrapers, migrating databases, or integrating AI scoring — without rewriting the rest of the system.


---

### 9. Security & Ethics
- Store all credentials securely in `.env`.
- Respect Axiom’s Terms of Service and rate limits.
- Include disclaimer: data collected for internal analytics only.
- Avoid exposing wallet addresses publicly in reports.

---

### 10. Future Phases

| Phase | Description |
|--------|-------------|
| **Phase 2** | AI-based scoring system (0–100) using statistical and behavioral models. |
| **Phase 3** | LLM-based summarization generating concise reports on each token. |
| **Phase 4** | Dashboard and automation with alerts and performance tracking. |
| **Phase 5** | Expansion to other blockchains and automated trading signals. |

---

### 11. Deliverables
1. **Scraper modules:** `pulse_scraper.py`, `tracker_scraper.py`  
2. **Data schema:** `schema.sql` or ORM equivalent  
3. **CLI tool:** `run_scrape.py`  
4. **Config files:** `.env`, `config.yaml`, `AGENTS.md`, `User Rules`  
5. **Docs:** Setup guide, run instructions, and README  
6. **Tests:** Parser validation, dry-run scraping with fixtures  
7. **Logs and samples:** Initial output JSONL/CSV and database snapshot

---

### 12. Timeline (5-Day Sprint)

| Day | Task |
|-----|------|
| **Day 1** | Setup repo, dependencies, Playwright environment, session storage |
| **Day 2** | Implement Pulse scraper + network intercept |
| **Day 3** | Implement Trackers scraper + storage models |
| **Day 4** | Validation, dedupe, error handling, CLI integration |
| **Day 5** | Testing, documentation, dry run, performance tuning |

---

### 13. Risks & Mitigations
| Risk | Mitigation |
|------|-------------|
| Axiom UI changes | JSON-first scraping, modular parsers |
| Anti-scraping measures | Add rate limiting and session management |
| Inconsistent JSON fields | Pydantic validation and default fallbacks |
| Network errors | Retry with exponential backoff |
| Session expiration | One-time login automation script |

---

### 14. Approval
**Owner:** Fyodor Golovin  
**Phase:** 1 (MVP – Data Ingestion)  
**Status:** In Development  
**Next Review:** After completion of Pulse + Trackers scraper testing
```
