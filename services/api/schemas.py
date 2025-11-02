"""
Pydantic schemas for API request/response models.

Extends core models with API-specific validation and formatting.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from axiom.core.models import TokenOverview, TokenPulseSnapshot, TokenTrackerSummary


class TokenListParams(BaseModel):
    """Query parameters for token list endpoint."""

    chain: str = Field(default="sol", description="Chain identifier")
    limit: int = Field(default=100, ge=1, le=500, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    sort_by: str = Field(default="last_seen_at", description="Sort field")
    order: str = Field(default="desc", description="Sort order (asc/desc)")


class TokenListResponse(BaseModel):
    """Response model for token list endpoint."""

    tokens: list[TokenOverview]
    total: int = Field(..., description="Total number of tokens available")
    limit: int
    offset: int


class PulseSnapshotListParams(BaseModel):
    """Query parameters for pulse snapshot list endpoint."""

    limit: int = Field(default=100, ge=1, le=500, description="Maximum number of results")


class PulseSnapshotListResponse(BaseModel):
    """Response model for pulse snapshot list endpoint."""

    snapshots: list[TokenPulseSnapshot]
    count: int


class TrackerSummaryResponse(BaseModel):
    """Response model for tracker summary endpoint."""

    summary: TokenTrackerSummary


class SearchParams(BaseModel):
    """Query parameters for search endpoint."""

    q: str = Field(..., min_length=1, max_length=200, description="Search query")
    chain: str = Field(default="sol", description="Chain identifier")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    include_external: bool = Field(
        default=True, description="Include results from external sources (Moralis)"
    )


class SearchResult(BaseModel):
    """Single search result."""

    ca: str = Field(..., description="Contract address")
    chain: str = Field(..., description="Chain identifier")
    token_name: Optional[str] = Field(None, description="Token name")
    symbol: Optional[str] = Field(None, description="Token symbol")
    source: str = Field(..., description="Data source (local/moralis)")
    score: Optional[float] = Field(None, description="Relevance or quality score")
    price_usd: Optional[float] = Field(None, description="Current price in USD")
    volume_usd_24h: Optional[float] = Field(None, description="24h volume in USD")


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    results: list[SearchResult]
    count: int
    query: str
    sources: list[str] = Field(..., description="Data sources included in results")


class FavoriteRequest(BaseModel):
    """Request model for adding favorite."""

    ca: str = Field(..., description="Contract address to favorite")
    chain: str = Field(default="sol", description="Chain identifier")


class FavoriteResponse(BaseModel):
    """Response model for favorite operation."""

    user_id: str
    ca: str
    chain: str
    favorited_at: datetime


class FavoriteListResponse(BaseModel):
    """Response model for favorites list."""

    favorites: list[FavoriteResponse]
    count: int


class ComparisonRequest(BaseModel):
    """Request model for creating comparison."""

    name: str = Field(..., min_length=1, max_length=100, description="Comparison name")
    token_addresses: list[str] = Field(
        ..., min_items=2, max_items=10, description="List of contract addresses to compare"
    )
    chain: str = Field(default="sol", description="Chain identifier")


class ComparisonResponse(BaseModel):
    """Response model for comparison."""

    comparison_id: str
    user_id: str
    name: str
    token_addresses: list[str]
    chain: str
    created_at: datetime
    updated_at: datetime


class ComparisonListResponse(BaseModel):
    """Response model for comparisons list."""

    comparisons: list[ComparisonResponse]
    count: int


class AlertRequest(BaseModel):
    """Request model for creating alert."""

    ca: str = Field(..., description="Contract address to monitor")
    chain: str = Field(default="sol", description="Chain identifier")
    alert_type: str = Field(
        ..., description="Alert type (price_change, volume_spike, new_listing, etc.)"
    )
    threshold: Optional[float] = Field(None, description="Threshold value for trigger")
    enabled: bool = Field(default=True, description="Alert enabled status")


class AlertResponse(BaseModel):
    """Response model for alert."""

    alert_id: str
    user_id: str
    ca: str
    chain: str
    alert_type: str
    threshold: Optional[float]
    enabled: bool
    created_at: datetime
    last_triggered_at: Optional[datetime]


class AlertListResponse(BaseModel):
    """Response model for alerts list."""

    alerts: list[AlertResponse]
    count: int


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")
    cache: str = Field(..., description="Cache connection status")
    timestamp: datetime = Field(..., description="Current server time")
