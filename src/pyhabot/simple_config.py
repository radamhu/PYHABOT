"""
Simplified configuration management for PYHABOT.

This module provides typed configuration loading from environment variables
and .env files without the integration pattern.
"""

import os
from typing import Optional, List
from pathlib import Path

from dotenv import load_dotenv

from .logging import get_logger

logger = get_logger(__name__)


class SimpleConfig:
    """Simplified configuration class for PYHABOT without integration requirements."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration from environment variables."""
        # Load .env file if specified
        if env_file:
            load_dotenv(env_file)
        else:
            # Look for .env in current directory and parent directories
            env_path = Path.cwd()
            while env_path != env_path.parent:
                env_file_path = env_path / ".env"
                if env_file_path.exists():
                    load_dotenv(env_file_path)
                    break
                env_path = env_path.parent
        
        self._load_config()
        logger.info("Simple configuration loaded successfully")
    
    def _load_config(self) -> None:
        """Load and validate all configuration values."""
        # Optional configuration with defaults
        self.persistent_data_path: str = os.getenv("PERSISTENT_DATA_PATH", "./persistent_data")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_format: str = os.getenv("LOG_FORMAT", "text")  # text or json
        
        # Scraping configuration
        self.scrape_interval: int = self._get_int_env("SCRAPE_INTERVAL", 300, 
            "Scraping interval in seconds")
        self.scrape_jitter_min: int = self._get_int_env("SCRAPE_JITTER_MIN", 0,
            "Minimum jitter for scraping in seconds")
        self.scrape_jitter_max: int = self._get_int_env("SCRAPE_JITTER_MAX", 60,
            "Maximum jitter for scraping in seconds")
        self.max_retries: int = self._get_int_env("MAX_RETRIES", 3,
            "Maximum number of retries for failed requests")
        
        # Request delays for scraping
        self.request_delay_min: float = self._get_float_env("REQUEST_DELAY_MIN", 1.0,
            "Minimum delay between requests in seconds")
        self.request_delay_max: float = self._get_float_env("REQUEST_DELAY_MAX", 3.0,
            "Maximum delay between requests in seconds")
        
        # User agents for scraping
        self.user_agents: List[str] = self._get_list_env("USER_AGENTS", [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
        ], "List of user agents for scraping")
        
        # Validate configuration
        self._validate_config()
    
    def _get_int_env(self, key: str, default: int, description: str) -> int:
        """Get an integer environment variable with default."""
        value = os.getenv(key)
        if value is None:
            return default
        
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}, using default: {default}")
            return default
    
    def _get_float_env(self, key: str, default: float, description: str) -> float:
        """Get a float environment variable with default."""
        value = os.getenv(key)
        if value is None:
            return default
        
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Invalid float value for {key}: {value}, using default: {default}")
            return default
    
    def _get_list_env(self, key: str, default: List[str], description: str) -> List[str]:
        """Get a list environment variable with default."""
        value = os.getenv(key)
        if value is None:
            return default
        
        # Split by comma and strip whitespace
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of: {valid_log_levels}")
        
        # Validate log format
        valid_log_formats = ["text", "json"]
        if self.log_format not in valid_log_formats:
            raise ValueError(f"Invalid log format: {self.log_format}. Must be one of: {valid_log_formats}")
        
        # Validate scraping intervals
        if self.scrape_interval <= 0:
            raise ValueError(f"Scrape interval must be positive: {self.scrape_interval}")
        
        if self.scrape_jitter_min < 0:
            raise ValueError(f"Scrape jitter min must be non-negative: {self.scrape_jitter_min}")
        
        if self.scrape_jitter_max < self.scrape_jitter_min:
            raise ValueError(f"Scrape jitter max must be >= min: {self.scrape_jitter_max} < {self.scrape_jitter_min}")
        
        if self.max_retries < 0:
            raise ValueError(f"Max retries must be non-negative: {self.max_retries}")
        
        # Validate request delays
        if self.request_delay_min < 0:
            raise ValueError(f"Request delay min must be non-negative: {self.request_delay_min}")
        
        if self.request_delay_max < self.request_delay_min:
            raise ValueError(f"Request delay max must be >= min: {self.request_delay_max} < {self.request_delay_min}")
        
        # Validate user agents
        if not self.user_agents:
            raise ValueError("At least one user agent must be configured")
        
        logger.debug("Simple configuration validation passed")
    
    def __str__(self) -> str:
        """Return string representation of configuration."""
        return (f"SimpleConfig(log_level={self.log_level}, "
                f"scrape_interval={self.scrape_interval}s)")
    
    def __repr__(self) -> str:
        """Return detailed string representation of configuration."""
        return (f"SimpleConfig("
                f"persistent_data_path={self.persistent_data_path!r}, "
                f"log_level={self.log_level!r}, "
                f"log_format={self.log_format!r}, "
                f"scrape_interval={self.scrape_interval}, "
                f"scrape_jitter_min={self.scrape_jitter_min}, "
                f"scrape_jitter_max={self.scrape_jitter_max}, "
                f"max_retries={self.max_retries}, "
                f"request_delay_min={self.request_delay_min}, "
                f"request_delay_max={self.request_delay_max}, "
                f"user_agents_count={len(self.user_agents)})")