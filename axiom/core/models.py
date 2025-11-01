"""
Pydantic data models for Axiom scraper.

All timestamps are normalized to EET (Eastern European Time, UTC+2).
All prices are normalized to USD.
"""

from datetime import datetime
from typing import Literal, Optional

import pytz
from pydantic import BaseModel, Field, field_validator


# EET timezone (UTC+2)
EET = pytz.timezone("Europe/Athens")


class RunMeta(BaseModel):
    """Metadata for a scraper run."""
    
    run_id: str = Field(..., description="Unique run identifier (UUID or timestamp-based)")
    mode: Literal["pulse", "trackers", "all"] = Field(..., description="Scraper mode")
    started_at: datetime = Field(..., description="Run start time (EET)")
    finished_at: Optional[datetime] = Field(None, description="Run finish time (EET)")
    status: Literal["running", "success", "failed"] = Field(
        default="running", description="Run status"
    )
    config_json: str = Field(..., description="JSON-serialized configuration")
    config_hash: str = Field(..., description="Hash of configuration for comparison")
    source_version: Optional[str] = Field(None, description="Git commit SHA or version tag")
    error_count: int = Field(default=0, description="Number of errors encountered")
    items_inserted: int = Field(default=0, description="Pulse items inserted")
    items_deduped: int = Field(default=0, description="Pulse items deduplicated")
    events_inserted: int = Field(default=0, description="Tracker events inserted")
    events_deduped: int = Field(default=0, description="Tracker events deduplicated")
    duration_ms: Optional[int] = Field(None, description="Run duration in milliseconds")
    
    @field_validator("started_at", "finished_at", mode="before")
    @classmethod
    def ensure_eet_timezone(cls, v):
        """Ensure all datetimes are in EET."""
        if v is None:
            return v
        if isinstance(v, str):
            # Parse ISO string
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        elif isinstance(v, datetime):
            dt = v
        else:
            raise ValueError(f"Invalid datetime value: {v}")
        
        # Convert to EET
        if dt.tzinfo is None:
            # Assume UTC if naive
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class PulseItem(BaseModel):
    """
    A token snapshot from Pulse feed.
    
    Deduplication key: (ca, segment, floor_minute)
    """
    
    run_id: str = Field(..., description="Associated run ID")
    ca: str = Field(..., description="Contract address (lowercased)")
    segment: str = Field(..., description="Segment category (e.g., 'new', 'top', 'rising')")
    floor_minute: datetime = Field(..., description="Minute bucket (EET, truncated to minute)")
    floor_price: Optional[float] = Field(None, description="Floor price in USD")
    token_name: Optional[str] = Field(None, description="Token name")
    symbol: Optional[str] = Field(None, description="Token symbol")
    source: Literal["pulse"] = Field(default="pulse", description="Data source")
    raw_json: Optional[str] = Field(None, description="Raw JSON payload for debugging")
    scraped_at: datetime = Field(..., description="Timestamp when scraped (EET)")
    
    @field_validator("ca", mode="before")
    @classmethod
    def normalize_ca(cls, v):
        """Normalize contract address to lowercase."""
        if v:
            return str(v).lower().strip()
        return v
    
    @field_validator("floor_minute", "scraped_at", mode="before")
    @classmethod
    def ensure_eet_datetime(cls, v):
        """Ensure datetime is in EET and floor_minute is truncated."""
        if v is None:
            return v
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        elif isinstance(v, datetime):
            dt = v
        else:
            raise ValueError(f"Invalid datetime value: {v}")
        
        # Convert to EET
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)
    
    @field_validator("floor_minute")
    @classmethod
    def truncate_to_minute(cls, v):
        """Truncate floor_minute to the start of the minute."""
        if v:
            return v.replace(second=0, microsecond=0)
        return v
    
    @field_validator("segment", mode="before")
    @classmethod
    def normalize_segment(cls, v):
        """Normalize segment to lowercase."""
        if v:
            return str(v).lower().strip()
        return v


class TrackerEvent(BaseModel):
    """
    A wallet activity event from Trackers feed.
    
    Deduplication key: (wallet, ca, action, tx_time)
    """
    
    run_id: str = Field(..., description="Associated run ID")
    wallet: str = Field(..., description="Wallet address (lowercased)")
    ca: str = Field(..., description="Contract address (lowercased)")
    action: str = Field(..., description="Action type (e.g., 'buy', 'sell', 'add_liquidity')")
    tx_time: datetime = Field(..., description="Transaction time (EET)")
    tx_sig: Optional[str] = Field(None, description="Transaction signature/hash")
    amount: Optional[float] = Field(None, description="Amount traded")
    amount_unit: Optional[str] = Field(None, description="Unit of amount (e.g., 'SOL', 'tokens')")
    price: Optional[float] = Field(None, description="Price in USD at time of transaction")
    src_url: Optional[str] = Field(None, description="Source URL for debugging")
    source: Literal["trackers"] = Field(default="trackers", description="Data source")
    raw_json: Optional[str] = Field(None, description="Raw JSON payload for debugging")
    scraped_at: datetime = Field(..., description="Timestamp when scraped (EET)")
    
    @field_validator("wallet", "ca", mode="before")
    @classmethod
    def normalize_addresses(cls, v):
        """Normalize addresses to lowercase."""
        if v:
            return str(v).lower().strip()
        return v
    
    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, v):
        """Normalize action to lowercase."""
        if v:
            return str(v).lower().strip().replace(" ", "_")
        return v
    
    @field_validator("tx_time", "scraped_at", mode="before")
    @classmethod
    def ensure_eet_datetime(cls, v):
        """Ensure datetime is in EET."""
        if v is None:
            return v
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        elif isinstance(v, datetime):
            dt = v
        else:
            raise ValueError(f"Invalid datetime value: {v}")
        
        # Convert to EET
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


def eet_now() -> datetime:
    """Get current datetime in EET timezone."""
    return datetime.now(EET)
