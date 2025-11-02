"""
Tokens router for token-related read endpoints.

Provides endpoints for:
- GET /tokens - List all tokens with filtering
- GET /tokens/{ca} - Get detailed token information
- GET /tokens/{ca}/pulse - Get pulse snapshots for a token
- GET /tokens/{ca}/trackers - Get tracker activity summary for a token
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from axiom.core.db import Database
from axiom.core.models import TokenOverview, TokenPulseSnapshot, TokenTrackerSummary
from services.api.cache import cached
from services.api.config import settings
from services.api.dependencies import get_database, limiter
from services.api.schemas import (
    PulseSnapshotListResponse,
    TokenListResponse,
    TrackerSummaryResponse,
)

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("", response_model=TokenListResponse)
@cached(settings.cache_ttl_medium, namespace="tokens:list")
@limiter.limit(settings.rate_limit_default)
async def list_tokens(
    chain: str = Query(default="sol", description="Chain identifier"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results to skip"),
    db: Database = Depends(get_database),
) -> TokenListResponse:
    """
    List tokens with metrics and summaries.

    Args:
        chain: Chain identifier (default: sol)
        limit: Maximum number of results (1-500)
        offset: Number of results to skip
        db: Database connection

    Returns:
        TokenListResponse with list of tokens
    """
    tokens_data = db.list_tokens(chain=chain, limit=limit, offset=offset)

    # Count total tokens
    conn = db.connect()
    total = conn.execute("SELECT COUNT(*) FROM tokens WHERE chain = ?", [chain]).fetchone()[0]

    tokens = [TokenOverview(**token) for token in tokens_data]

    return TokenListResponse(tokens=tokens, total=total, limit=limit, offset=offset)


@router.get("/{ca}", response_model=TokenOverview)
@cached(settings.cache_ttl_short, namespace="tokens:detail")
@limiter.limit(settings.rate_limit_default)
async def get_token(
    ca: str,
    chain: str = Query(default="sol", description="Chain identifier"),
    db: Database = Depends(get_database),
) -> TokenOverview:
    """
    Get detailed token information by contract address.

    Args:
        ca: Contract address
        chain: Chain identifier (default: sol)
        db: Database connection

    Returns:
        TokenOverview with complete token information

    Raises:
        HTTPException: 404 if token not found
    """
    token_data = db.get_token(ca=ca.lower(), chain=chain)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {ca} not found on chain {chain}",
        )

    return TokenOverview(**token_data)


@router.get("/{ca}/pulse", response_model=PulseSnapshotListResponse)
@cached(settings.cache_ttl_short, namespace="tokens:pulse")
@limiter.limit(settings.rate_limit_default)
async def get_token_pulse(
    ca: str,
    chain: str = Query(default="sol", description="Chain identifier"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum snapshots"),
    db: Database = Depends(get_database),
) -> PulseSnapshotListResponse:
    """
    Get pulse snapshots for a specific token.

    Args:
        ca: Contract address
        chain: Chain identifier (default: sol)
        limit: Maximum number of snapshots (1-500)
        db: Database connection

    Returns:
        PulseSnapshotListResponse with pulse snapshots

    Raises:
        HTTPException: 404 if token not found
    """
    # Check if token exists
    token_data = db.get_token(ca=ca.lower(), chain=chain)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {ca} not found on chain {chain}",
        )

    pulse_data = db.get_token_pulse(ca=ca.lower(), chain=chain, limit=limit)
    snapshots = [TokenPulseSnapshot(**snapshot) for snapshot in pulse_data]

    return PulseSnapshotListResponse(snapshots=snapshots, count=len(snapshots))


@router.get("/{ca}/trackers", response_model=TrackerSummaryResponse)
@cached(settings.cache_ttl_short, namespace="tokens:trackers")
@limiter.limit(settings.rate_limit_default)
async def get_token_trackers(
    ca: str,
    chain: str = Query(default="sol", description="Chain identifier"),
    db: Database = Depends(get_database),
) -> TrackerSummaryResponse:
    """
    Get tracker activity summary for a specific token.

    Args:
        ca: Contract address
        chain: Chain identifier (default: sol)
        db: Database connection

    Returns:
        TrackerSummaryResponse with aggregated tracker activity

    Raises:
        HTTPException: 404 if token not found
    """
    # Check if token exists
    token_data = db.get_token(ca=ca.lower(), chain=chain)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {ca} not found on chain {chain}",
        )

    tracker_data = db.get_token_trackers(ca=ca.lower(), chain=chain)
    summary = TokenTrackerSummary(**tracker_data)

    return TrackerSummaryResponse(summary=summary)
