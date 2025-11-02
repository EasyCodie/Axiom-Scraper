"""
FastAPI main application entry point.

Integrates routers, middleware, caching, and CORS.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from axiom.core.db import Database
from axiom.core.models import eet_now
from services.api.cache import init_cache
from services.api.config import settings
from services.api.dependencies import limiter
from services.api.routers import search, tokens, user
from services.api.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format=(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        if settings.log_format == "text"
        else "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for startup/shutdown."""
    # Startup: Initialize Redis cache
    redis = None
    try:
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        await redis.ping()
        init_cache(redis)
        logger.info(f"Redis cache initialized: {settings.redis_url}")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}. Running without cache.")
        init_cache(None)

    # Initialize database schema if needed
    try:
        db = Database(db_path=settings.database_path)
        conn = db.connect()
        logger.info(f"Database connected: {settings.database_path}")

        # Ensure user-related tables exist
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id VARCHAR PRIMARY KEY,
                email VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_favorites (
                user_id VARCHAR NOT NULL,
                ca VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, ca, chain),
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_comparisons (
                comparison_id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                token_addresses VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_alerts (
                alert_id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                ca VARCHAR NOT NULL,
                chain VARCHAR NOT NULL,
                alert_type VARCHAR NOT NULL,
                threshold DOUBLE,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_triggered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            );
            """
        )

        db.close()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    yield

    # Shutdown: Close Redis connection
    if redis:
        await redis.close()
        logger.info("Redis connection closed")


# Create FastAPI app
app = FastAPI(
    title="Axiom Token Analytics API",
    description="FastAPI service for Axiom meme-coin scoring and token analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse with service status
    """
    # Check database connection
    db_status = "ok"
    try:
        db = Database(db_path=settings.database_path)
        db.connect()
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    # Check Redis connection
    cache_status = "ok"
    try:
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        await redis.ping()
        await redis.close()
    except Exception as e:
        cache_status = f"error: {str(e)}"
        logger.warning(f"Cache health check failed: {e}")

    return HealthResponse(
        status="healthy" if db_status == "ok" else "degraded",
        version="1.0.0",
        database=db_status,
        cache=cache_status,
        timestamp=eet_now(),
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "service": "Axiom Token Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(tokens.router)
app.include_router(search.router)
app.include_router(user.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
