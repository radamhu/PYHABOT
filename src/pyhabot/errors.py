"""
Custom exceptions and error handling for PYHABOT.

This module defines custom exception classes and error handling utilities
for better error categorization and debugging.
"""

from typing import Optional, Any


class PyhabotError(Exception):
    """Base exception class for all PYHABOT errors."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """Initialize exception with message and optional details.
        
        Args:
            message: Error message
            details: Additional error context as key-value pairs
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return string representation of error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConfigurationError(PyhabotError):
    """Raised when there's an error in configuration."""
    pass


class ScrapingError(PyhabotError):
    """Raised when there's an error during web scraping."""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        """Initialize scraping error with URL and status context.
        
        Args:
            message: Error message
            url: URL that was being scraped
            status_code: HTTP status code if applicable
            **kwargs: Additional error details
        """
        details = kwargs
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(message, details)
        self.url = url
        self.status_code = status_code


class DatabaseError(PyhabotError):
    """Raised when there's an error in database operations."""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None, **kwargs):
        """Initialize database error with operation context.
        
        Args:
            message: Error message
            operation: Database operation that failed
            table: Table name if applicable
            **kwargs: Additional error details
        """
        details = kwargs
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        
        super().__init__(message, details)
        self.operation = operation
        self.table = table


class IntegrationError(PyhabotError):
    """Raised when there's an error with chat platform integrations."""
    
    def __init__(self, message: str, integration: Optional[str] = None, channel: Optional[str] = None, **kwargs):
        """Initialize integration error with platform context.
        
        Args:
            message: Error message
            integration: Integration name (discord, telegram, terminal)
            channel: Channel/user identifier if applicable
            **kwargs: Additional error details
        """
        details = kwargs
        if integration:
            details["integration"] = integration
        if channel:
            details["channel"] = channel
        
        super().__init__(message, details)
        self.integration = integration
        self.channel = channel


class WebhookError(PyhabotError):
    """Raised when there's an error with webhook notifications."""
    
    def __init__(self, message: str, webhook_url: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        """Initialize webhook error with URL and status context.
        
        Args:
            message: Error message
            webhook_url: Webhook URL that failed
            status_code: HTTP status code if applicable
            **kwargs: Additional error details
        """
        details = kwargs
        if webhook_url:
            details["webhook_url"] = webhook_url
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(message, details)
        self.webhook_url = webhook_url
        self.status_code = status_code


class ValidationError(PyhabotError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
        """Initialize validation error with field context.
        
        Args:
            message: Error message
            field: Field name that failed validation
            value: Value that failed validation
            **kwargs: Additional error details
        """
        details = kwargs
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(message, details)
        self.field = field
        self.value = value


class RetryableError(PyhabotError):
    """Base class for errors that can be retried."""
    
    def __init__(self, message: str, retry_after: Optional[float] = None, max_retries: Optional[int] = None, **kwargs):
        """Initialize retryable error with retry context.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retry
            max_retries: Maximum number of retries allowed
            **kwargs: Additional error details
        """
        details = kwargs
        if retry_after is not None:
            details["retry_after"] = retry_after
        if max_retries is not None:
            details["max_retries"] = max_retries
        
        super().__init__(message, details)
        self.retry_after = retry_after
        self.max_retries = max_retries


class NetworkError(RetryableError):
    """Raised when there's a network-related error."""
    
    def __init__(self, message: str, url: Optional[str] = None, timeout: Optional[float] = None, **kwargs):
        """Initialize network error with network context.
        
        Args:
            message: Error message
            url: URL that failed
            timeout: Timeout duration if applicable
            **kwargs: Additional error details
        """
        details = kwargs
        if url:
            details["url"] = url
        if timeout is not None:
            details["timeout"] = timeout
        
        super().__init__(message, **kwargs)
        self.url = url
        self.timeout = timeout


def handle_error(error: Exception, logger) -> None:
    """Handle and log errors appropriately based on type.
    
    Args:
        error: Exception to handle
        logger: Logger instance to use for logging
    """
    if isinstance(error, PyhabotError):
        # Log our custom errors with details
        logger.error(f"{error.__class__.__name__}: {error.message}", extra=error.details)
    else:
        # Log unexpected errors with full traceback
        logger.exception(f"Unexpected error: {error}")


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.
    
    Args:
        error: Exception to check
        
    Returns:
        True if error should be retried, False otherwise
    """
    return isinstance(error, RetryableError) or isinstance(error, (NetworkError, ScrapingError))