"""
Configuration loader with precedence: CLI args > config.yaml > .env defaults.

Provides a unified Config object that merges settings from multiple sources.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load .env file if it exists
load_dotenv()


class BrowserConfig(BaseModel):
    """Browser configuration for Playwright."""
    
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    timeout: int = 30000  # milliseconds


class PulseConfig(BaseModel):
    """Configuration for Pulse scraper."""
    
    url: str = "https://axiom.trade/pulse?chain=sol"
    max_rows: int = 20
    scroll_timeout: int = 20
    delay_between_scrolls: int = 1
    api_patterns: List[str] = Field(default_factory=lambda: [".*api.*pulse.*", ".*graphql.*"])
    selectors: Dict[str, str] = Field(
        default_factory=lambda: {
            "token_row": "[data-testid='token-row'], .token-item, tr[data-token]",
            "token_name": "[data-testid='token-name'], .token-name",
            "contract_address": "[data-testid='ca'], .contract-address",
            "price": "[data-testid='price'], .price",
        }
    )


class TrackerConfig(BaseModel):
    """Configuration for Trackers scraper."""
    
    url: str = "https://axiom.trade/trackers?chain=sol"
    max_events: int = 100
    stream_timeout: int = 30
    api_patterns: List[str] = Field(
        default_factory=lambda: [".*api.*tracker.*", ".*api.*wallet.*", ".*websocket.*"]
    )
    selectors: Dict[str, str] = Field(
        default_factory=lambda: {
            "event_row": "[data-testid='tracker-event'], .tracker-event, tr[data-event]",
            "wallet": "[data-testid='wallet'], .wallet-address",
            "action": "[data-testid='action'], .action",
        }
    )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    
    concurrent_requests: int = 5
    delay_seconds: int = 2
    max_retries: int = 3
    backoff_factor: int = 2


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    path: str = "data/axiom.duckdb"
    batch_size: int = 200


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = "INFO"
    format: str = "json"
    dir: str = "logs"
    rotation: str = "1 day"
    retention: str = "14 days"


class Config(BaseModel):
    """Main configuration object."""
    
    chain: str = "sol"
    timezone: str = "Europe/Athens"
    currency: str = "USD"
    
    pulse: PulseConfig = Field(default_factory=PulseConfig)
    tracker: TrackerConfig = Field(default_factory=TrackerConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Runtime overrides (from CLI)
    storage_state_path: str = "storage_state.json"
    git_sha: Optional[str] = None
    
    @classmethod
    def load(
        cls,
        config_path: str = "configs/config.yaml",
        cli_overrides: Optional[Dict[str, Any]] = None,
    ) -> "Config":
        """
        Load configuration with precedence: CLI > YAML > ENV.
        
        Args:
            config_path: Path to YAML config file
            cli_overrides: Dictionary of CLI argument overrides
            
        Returns:
            Loaded Config object
        """
        # Start with defaults (from BaseModel defaults)
        config_dict: Dict[str, Any] = {}
        
        # Load from YAML if exists
        yaml_path = Path(config_path)
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    config_dict.update(yaml_data)
        
        # Overlay environment variables
        env_overrides = {
            "database": {"path": os.getenv("DATABASE_PATH", config_dict.get("database", {}).get("path"))},
            "storage_state_path": os.getenv("STORAGE_STATE_PATH", "storage_state.json"),
            "browser": {
                "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
                "timeout": int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000")),
            },
            "pulse": {"max_rows": int(os.getenv("MAX_PULSE_ROWS", "20"))},
            "tracker": {"max_events": int(os.getenv("MAX_TRACKER_EVENTS", "100"))},
            "rate_limit": {
                "concurrent_requests": int(os.getenv("RATE_LIMIT_CONCURRENT", "5")),
                "delay_seconds": int(os.getenv("SCRAPE_DELAY_SECONDS", "2")),
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "dir": os.getenv("LOG_DIR", "logs"),
            },
            "timezone": os.getenv("TIMEZONE", "Europe/Athens"),
            "git_sha": os.getenv("GIT_SHA"),
        }
        
        # Deep merge env overrides
        config_dict = _deep_merge(config_dict, env_overrides)
        
        # Apply CLI overrides (highest priority)
        if cli_overrides:
            config_dict = _deep_merge(config_dict, cli_overrides)
        
        return cls(**config_dict)
    
    def to_json(self) -> str:
        """Serialize config to JSON string."""
        return self.model_dump_json(indent=2)
    
    def compute_hash(self) -> str:
        """Compute hash of configuration for comparison."""
        config_json = self.model_dump_json(sort_keys=True)
        return hashlib.sha256(config_json.encode()).hexdigest()[:16]


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with override taking precedence.
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        elif value is not None:  # Only override if not None
            result[key] = value
    
    return result


def load_config(
    config_path: str = "configs/config.yaml",
    cli_overrides: Optional[Dict[str, Any]] = None,
) -> Config:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Path to YAML config file
        cli_overrides: Dictionary of CLI argument overrides
        
    Returns:
        Loaded Config object
    """
    return Config.load(config_path, cli_overrides)
