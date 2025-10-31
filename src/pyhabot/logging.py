"""
Centralized logging configuration for PYHABOT.

This module provides a centralized logger factory with support for
different log levels and output formats (text/JSON).
"""

import logging
import os
import sys
from typing import Optional

# Global logger cache to avoid duplicate handlers
_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured logger instance
    """
    # Return cached logger if available
    if name in _loggers:
        return _loggers[name]
    
    # Create new logger
    logger = logging.getLogger(name)
    
    # Only configure if no handlers exist (avoid duplicate logs)
    if not logger.handlers:
        _configure_logger(logger)
    
    # Cache the logger
    _loggers[name] = logger
    return logger


def _configure_logger(logger: logging.Logger) -> None:
    """Configure a logger with appropriate handlers and formatters."""
    # Get configuration from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "text").lower()
    
    # Set log level
    level = getattr(logging, log_level, logging.INFO)
    logger.setLevel(level)
    
    # Create handler (stderr by default)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    
    # Create formatter based on format type
    if log_format == "json":
        formatter = _JsonFormatter()
    else:
        formatter = _TextFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False


class _TextFormatter(logging.Formatter):
    """Text formatter for human-readable logs."""
    
    def __init__(self) -> None:
        """Initialize text formatter."""
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text."""
        # Add context information if available
        if hasattr(record, 'watch_id'):
            record.msg = f"[watch_id={record.watch_id}] {record.msg}"
        
        if hasattr(record, 'url'):
            record.msg = f"[url={record.url}] {record.msg}"
        
        if hasattr(record, 'corr_id'):
            record.msg = f"[corr_id={record.corr_id}] {record.msg}"
        
        return super().format(record)


class _JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        import time
        
        # Basic log fields
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context fields if available
        if hasattr(record, 'watch_id'):
            log_entry["watch_id"] = record.watch_id
        
        if hasattr(record, 'url'):
            log_entry["url"] = record.url
        
        if hasattr(record, 'corr_id'):
            log_entry["corr_id"] = record.corr_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add file and line info for debug level
        if record.levelno <= logging.DEBUG:
            log_entry.update({
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            })
        
        return json.dumps(log_entry, ensure_ascii=False)


def add_context(logger: logging.Logger, **kwargs) -> logging.LoggerAdapter:
    """Create a logger adapter with additional context fields.
    
    Args:
        logger: Base logger instance
        **kwargs: Context fields to add to all log messages
        
    Returns:
        LoggerAdapter with context
    """
    return _ContextLoggerAdapter(logger, kwargs)


class _ContextLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to log messages."""
    
    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Process log message to add context."""
        # Add context to extra dict
        extra = kwargs.get('extra', {})
        for key, value in self.extra.items():
            extra[key] = value
        kwargs['extra'] = extra
        
        return msg, kwargs


def configure_root_logger() -> None:
    """Configure the root logger for application-wide logging."""
    # This ensures that any libraries using the root logger
    # also use our configuration
    root = logging.getLogger()
    
    # Remove existing handlers to avoid duplicates
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    
    # Configure with our settings
    _configure_logger(root)
    
    # Set root logger level to DEBUG to allow all levels through
    # (individual loggers will control their actual level)
    root.setLevel(logging.DEBUG)