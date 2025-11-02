# Axiom Token Analytics API

FastAPI service providing REST endpoints for Axiom meme-coin scoring and token analytics.

## Features

- **Token Endpoints**: List tokens, get detailed token information, pulse snapshots, and tracker activity
- **Search**: Multi-source search across local database and Moralis API
- **User Management**: Protected endpoints for favorites, comparisons, and alerts with Supabase JWT authentication
- **Caching**: Redis-backed caching with configurable TTLs (5-15 minutes)
- **Rate Limiting**: SlowAPI integration with per-endpoint limits
- **OpenAPI Docs**: Auto-generated interactive documentation at `/docs`

## Quick Start

### Installation

```bash
# Install dependencies
pip install -e .

# Or using the virtual environment
source .venv/bin/activate
pip install -e .
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database
API_DATABASE_PATH=data/axiom.duckdb

# Redis Cache
API_REDIS_URL=redis://localhost:6379/0

# Moralis API (optional)
API_MORALIS_API_KEY=your_moralis_api_key

# Supabase Auth (optional)
API_SUPABASE_URL=https://your-project.supabase.co
API_SUPABASE_JWT_SECRET=your_jwt_secret
```

### Running the Service

```bash
# Using the startup script
./scripts/run_api.sh

# Or directly with Python
python -m services.api

# Or with uvicorn for development
uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Public Endpoints

#### Tokens
- `GET /tokens` - List all tokens with metrics
- `GET /tokens/{ca}` - Get detailed token information
- `GET /tokens/{ca}/pulse` - Get pulse snapshots for a token
- `GET /tokens/{ca}/trackers` - Get tracker activity summary

#### Search
- `GET /search` - Search tokens across local DB and Moralis API

#### Health
- `GET /health` - Service health check
- `GET /` - API information

### Protected Endpoints (Require Authentication)

#### Favorites
- `GET /user/favorites` - List user's favorite tokens
- `POST /user/favorites` - Add token to favorites
- `DELETE /user/favorites/{ca}` - Remove from favorites

#### Comparisons
- `GET /user/comparisons` - List user's token comparisons
- `POST /user/comparisons` - Create new comparison
- `DELETE /user/comparisons/{comparison_id}` - Delete comparison

#### Alerts
- `GET /user/alerts` - List user's price alerts
- `POST /user/alerts` - Create new alert
- `PATCH /user/alerts/{alert_id}` - Update alert
- `DELETE /user/alerts/{alert_id}` - Delete alert

## Authentication

Protected endpoints require a Supabase JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/user/favorites
```

## Caching

The API uses fastapi-cache2 with Redis for response caching:
- Token lists: 10 minutes (configurable via `API_CACHE_TTL_MEDIUM`)
- Token details: 5 minutes (configurable via `API_CACHE_TTL_SHORT`)
- Search results: 10 minutes

## Rate Limiting

Default rate limits:
- General endpoints: 100 requests/minute
- Search endpoint: 20 requests/minute

Configure via environment variables:
- `API_RATE_LIMIT_DEFAULT=100/minute`
- `API_RATE_LIMIT_SEARCH=20/minute`

## Testing

```bash
# Run all API tests
pytest tests/api/

# Run specific test file
pytest tests/api/test_tokens.py

# Run with coverage
pytest tests/api/ --cov=services.api
```

## Architecture

```
services/api/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── dependencies.py      # Dependency injection (DB, auth, rate limiting)
├── cache.py             # Caching utilities
├── external.py          # External API clients (Moralis)
├── schemas.py           # Pydantic request/response models
└── routers/
    ├── tokens.py        # Token endpoints
    ├── search.py        # Search endpoints
    └── user.py          # Protected user endpoints
```

## Environment Variables

See `.env.example` for all available configuration options.

Key settings:
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `API_DATABASE_PATH`: Path to DuckDB database
- `API_REDIS_URL`: Redis connection URL
- `API_MORALIS_API_KEY`: Moralis API key for external search
- `API_SUPABASE_JWT_SECRET`: Supabase JWT secret for authentication

## Development

For development with auto-reload:

```bash
API_RELOAD=true python -m services.api
```

## Production Deployment

For production, use multiple workers:

```bash
uvicorn services.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

Or use Gunicorn with Uvicorn workers:

```bash
gunicorn services.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```
