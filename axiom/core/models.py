"""
Pydantic data models for Axiom scraper.

All timestamps are normalized to EET (Eastern European Time, UTC+2).
All prices are normalized to USD.
"""

import json
from datetime import datetime
from typing import List, Literal, Optional

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


class UserProfile(BaseModel):
    """User profile information."""

    user_id: str = Field(..., description="Supabase user UUID")
    email: Optional[str] = Field(None, description="User email address")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    created_at: datetime = Field(..., description="Account creation timestamp (EET)")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp (EET)")
    preferences_json: Optional[str] = Field(None, description="User preferences as JSON string")

    @field_validator("created_at", "last_login_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class FavoriteToken(BaseModel):
    """User's favorite token."""

    user_id: str = Field(..., description="User UUID")
    ca: str = Field(..., description="Contract address (lowercased)")
    chain: str = Field(..., description="Chain identifier (e.g., 'sol')")
    added_at: datetime = Field(..., description="Timestamp when added (EET)")
    notes: Optional[str] = Field(None, description="User notes about the token")

    @field_validator("ca", mode="before")
    @classmethod
    def normalize_ca(cls, v):
        """Normalize contract address to lowercase."""
        if v:
            return str(v).lower().strip()
        return v

    @field_validator("added_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class Watchlist(BaseModel):
    """User's watchlist."""

    watchlist_id: str = Field(..., description="Unique watchlist identifier")
    user_id: str = Field(..., description="User UUID")
    name: str = Field(..., description="Watchlist name")
    description: Optional[str] = Field(None, description="Watchlist description")
    created_at: datetime = Field(..., description="Creation timestamp (EET)")
    updated_at: datetime = Field(..., description="Last update timestamp (EET)")
    is_public: bool = Field(default=False, description="Whether watchlist is public")

    @field_validator("created_at", "updated_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class WatchlistToken(BaseModel):
    """Token in a watchlist."""

    watchlist_id: str = Field(..., description="Watchlist identifier")
    ca: str = Field(..., description="Contract address (lowercased)")
    chain: str = Field(..., description="Chain identifier (e.g., 'sol')")
    added_at: datetime = Field(..., description="Timestamp when added (EET)")
    position: Optional[int] = Field(None, description="Display position in watchlist")
    notes: Optional[str] = Field(None, description="User notes about the token")

    @field_validator("ca", mode="before")
    @classmethod
    def normalize_ca(cls, v):
        """Normalize contract address to lowercase."""
        if v:
            return str(v).lower().strip()
        return v

    @field_validator("added_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class SavedComparison(BaseModel):
    """Saved token comparison."""

    comparison_id: str = Field(..., description="Unique comparison identifier")
    user_id: str = Field(..., description="User UUID")
    name: str = Field(..., description="Comparison name")
    description: Optional[str] = Field(None, description="Comparison description")
    created_at: datetime = Field(..., description="Creation timestamp (EET)")
    updated_at: datetime = Field(..., description="Last update timestamp (EET)")

    @field_validator("created_at", "updated_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class ComparisonToken(BaseModel):
    """Token in a comparison."""

    comparison_id: str = Field(..., description="Comparison identifier")
    ca: str = Field(..., description="Contract address (lowercased)")
    chain: str = Field(..., description="Chain identifier (e.g., 'sol')")
    position: int = Field(..., description="Position in comparison")
    added_at: datetime = Field(..., description="Timestamp when added (EET)")

    @field_validator("ca", mode="before")
    @classmethod
    def normalize_ca(cls, v):
        """Normalize contract address to lowercase."""
        if v:
            return str(v).lower().strip()
        return v

    @field_validator("added_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class Alert(BaseModel):
    """Alert definition."""

    alert_id: str = Field(..., description="Unique alert identifier")
    user_id: str = Field(..., description="User UUID")
    ca: str = Field(..., description="Contract address (lowercased)")
    chain: str = Field(..., description="Chain identifier (e.g., 'sol')")
    alert_type: str = Field(..., description="Alert type (e.g., 'price_above', 'price_below')")
    condition_json: str = Field(..., description="Alert condition as JSON string")
    is_active: bool = Field(default=True, description="Whether alert is active")
    created_at: datetime = Field(..., description="Creation timestamp (EET)")
    updated_at: datetime = Field(..., description="Last update timestamp (EET)")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger timestamp (EET)")
    trigger_count: int = Field(default=0, description="Number of times triggered")

    @field_validator("ca", mode="before")
    @classmethod
    def normalize_ca(cls, v):
        """Normalize contract address to lowercase."""
        if v:
            return str(v).lower().strip()
        return v

    @field_validator("created_at", "updated_at", "last_triggered_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class AlertChannel(BaseModel):
    """Alert delivery channel."""

    alert_id: str = Field(..., description="Alert identifier")
    channel_type: str = Field(..., description="Channel type (e.g., 'email', 'webhook', 'push')")
    channel_config_json: str = Field(..., description="Channel configuration as JSON string")
    is_enabled: bool = Field(default=True, description="Whether channel is enabled")


class AlertEvent(BaseModel):
    """Alert event (trigger and delivery history)."""

    event_id: str = Field(..., description="Unique event identifier")
    alert_id: str = Field(..., description="Alert identifier")
    triggered_at: datetime = Field(..., description="Trigger timestamp (EET)")
    condition_met_json: str = Field(..., description="Condition that was met as JSON string")
    delivery_status: str = Field(
        ..., description="Delivery status (e.g., 'pending', 'delivered', 'failed')"
    )
    delivery_attempts: int = Field(default=0, description="Number of delivery attempts")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp (EET)")
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")

    @field_validator("triggered_at", "delivered_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class TokenOverview(BaseModel):
    """Token overview response model with denormalized data."""

    ca: str = Field(..., description="Contract address")
    chain: str = Field(..., description="Chain identifier (e.g., 'sol')")
    token_name: Optional[str] = Field(None, description="Token name")
    symbol: Optional[str] = Field(None, description="Token symbol")
    first_seen_at: Optional[datetime] = Field(None, description="First appearance (EET)")
    last_seen_at: Optional[datetime] = Field(None, description="Last seen timestamp (EET)")
    last_pulse_at: Optional[datetime] = Field(None, description="Last pulse update (EET)")
    last_tracker_at: Optional[datetime] = Field(None, description="Last tracker activity (EET)")
    latest_segment: Optional[str] = Field(None, description="Latest pulse segment")
    latest_floor_price: Optional[float] = Field(None, description="Latest floor price (USD)")
    score: Optional[float] = Field(None, description="Axiom score (0-100)")
    price_usd: Optional[float] = Field(None, description="Current price (USD)")
    price_change_1h: Optional[float] = Field(None, description="1-hour price change (%)")
    price_change_6h: Optional[float] = Field(None, description="6-hour price change (%)")
    volume_usd_1h: Optional[float] = Field(None, description="1-hour volume (USD)")
    volume_usd_6h: Optional[float] = Field(None, description="6-hour volume (USD)")
    volume_usd_24h: Optional[float] = Field(None, description="24-hour volume (USD)")
    trade_count_1h: Optional[int] = Field(None, description="1-hour trade count")
    trade_count_6h: Optional[int] = Field(None, description="6-hour trade count")
    trade_count_24h: Optional[int] = Field(None, description="24-hour trade count")
    buy_sell_ratio: Optional[float] = Field(None, description="Buy/sell ratio")
    liquidity_score: Optional[float] = Field(None, description="Liquidity score")
    risk_flags: List[str] = Field(default_factory=list, description="Risk flags")
    sparkline: List[float] = Field(
        default_factory=list, description="Sparkline price points (newest last)"
    )
    headline: Optional[str] = Field(None, description="Summary headline")
    bullet_1: Optional[str] = Field(None, description="Summary bullet 1")
    bullet_2: Optional[str] = Field(None, description="Summary bullet 2")
    bullet_3: Optional[str] = Field(None, description="Summary bullet 3")
    bullet_4: Optional[str] = Field(None, description="Summary bullet 4")
    bullet_5: Optional[str] = Field(None, description="Summary bullet 5")
    sentiment: Optional[str] = Field(None, description="Sentiment indicator")

    @field_validator(
        "first_seen_at", "last_seen_at", "last_pulse_at", "last_tracker_at", mode="before"
    )
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
            return None

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)

    @field_validator("risk_flags", mode="before")
    @classmethod
    def parse_risk_flags(cls, v):
        """Parse risk flags from JSON string to list."""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return []
        return []

    @field_validator("sparkline", mode="before")
    @classmethod
    def parse_sparkline(cls, v):
        """Parse sparkline from JSON string to list."""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return []
        return []

    @field_validator("ca", mode="before")
    @classmethod
    def normalize_ca(cls, v):
        """Normalize contract address to lowercase."""
        if v is None:
            return v
        return str(v).lower().strip()

    @field_validator("latest_segment", mode="before")
    @classmethod
    def normalize_segment(cls, v):
        """Normalize latest segment to lowercase."""
        if v is None:
            return v
        return str(v).lower().strip()


class TokenPulseSnapshot(BaseModel):
    """Token pulse snapshot from pulse_items."""

    ca: str = Field(..., description="Contract address")
    chain: str = Field(default="sol", description="Chain identifier")
    segment: str = Field(..., description="Pulse segment")
    floor_minute: datetime = Field(..., description="Time bucket (EET)")
    floor_price: Optional[float] = Field(None, description="Floor price (USD)")
    token_name: Optional[str] = Field(None, description="Token name")
    symbol: Optional[str] = Field(None, description="Token symbol")
    run_id: str = Field(..., description="Scraper run ID")
    scraped_at: datetime = Field(..., description="Scraped timestamp (EET)")

    @field_validator("floor_minute", "scraped_at", mode="before")
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

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)


class TokenTrackerSummary(BaseModel):
    """Token tracker activity summary from tracker_events."""

    ca: str = Field(..., description="Contract address")
    chain: str = Field(default="sol", description="Chain identifier")
    trade_count: int = Field(default=0, description="Total trade count")
    unique_wallets: int = Field(default=0, description="Unique wallet count")
    buy_count: int = Field(default=0, description="Buy transaction count")
    sell_count: int = Field(default=0, description="Sell transaction count")
    total_volume_usd: Optional[float] = Field(None, description="Total volume (USD)")
    avg_price_usd: Optional[float] = Field(None, description="Average price (USD)")
    first_trade_at: Optional[datetime] = Field(None, description="First trade timestamp (EET)")
    last_trade_at: Optional[datetime] = Field(None, description="Last trade timestamp (EET)")
    top_actions: Optional[str] = Field(None, description="Most common actions (JSON)")

    @field_validator("first_trade_at", "last_trade_at", mode="before")
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
            return None

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(EET)
