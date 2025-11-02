"""
Custom exceptions for PYHABOT API.

This module defines custom exception classes for structured error responses
following RFC 7807 Problem Details for HTTP APIs.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException


class PyhabotAPIException(HTTPException):
    """Custom API exception with structured error responses."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.context = context or {}
        self.headers = headers
    
    def to_response_dict(self) -> Dict[str, Any]:
        """Convert exception to response dictionary."""
        response = {
            "error": self.detail,
            "error_code": self.error_code
        }
        
        if self.context:
            response["details"] = self.context
        
        return response


class WatchNotFoundError(PyhabotAPIException):
    """Exception raised when a watch is not found."""
    
    def __init__(self, watch_id: int):
        super().__init__(
            status_code=404,
            detail="Watch not found",
            error_code="WATCH_NOT_FOUND",
            context={"watch_id": watch_id}
        )


class AdvertisementNotFoundError(PyhabotAPIException):
    """Exception raised when an advertisement is not found."""
    
    def __init__(self, ad_id: int):
        super().__init__(
            status_code=404,
            detail="Advertisement not found",
            error_code="ADVERTISEMENT_NOT_FOUND",
            context={"ad_id": ad_id}
        )


class JobNotFoundError(PyhabotAPIException):
    """Exception raised when a job is not found."""
    
    def __init__(self, job_id: str):
        super().__init__(
            status_code=404,
            detail="Job not found",
            error_code="JOB_NOT_FOUND",
            context={"job_id": job_id}
        )


class InvalidURLError(PyhabotAPIException):
    """Exception raised when a URL is invalid."""
    
    def __init__(self, url: str, reason: str = "Invalid URL"):
        super().__init__(
            status_code=400,
            detail=f"Invalid URL: {reason}",
            error_code="INVALID_URL",
            context={"url": url, "reason": reason}
        )


class DuplicateWatchError(PyhabotAPIException):
    """Exception raised when trying to create a duplicate watch."""
    
    def __init__(self, url: str):
        super().__init__(
            status_code=409,
            detail="Watch already exists for this URL",
            error_code="DUPLICATE_WATCH",
            context={"url": url}
        )


class ServiceUnavailableError(PyhabotAPIException):
    """Exception raised when a required service is unavailable."""
    
    def __init__(self, service: str):
        super().__init__(
            status_code=503,
            detail=f"Service temporarily unavailable: {service}",
            error_code="SERVICE_UNAVAILABLE",
            context={"service": service}
        )


class ValidationError(PyhabotAPIException):
    """Exception raised for validation errors."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            status_code=422,
            detail=f"Validation failed for field: {field}",
            error_code="VALIDATION_ERROR",
            context={"field": field, "message": message}
        )


class JobProcessingError(PyhabotAPIException):
    """Exception raised when job processing fails."""
    
    def __init__(self, job_id: str, error_message: str):
        super().__init__(
            status_code=500,
            detail=f"Job processing failed: {error_message}",
            error_code="JOB_PROCESSING_ERROR",
            context={"job_id": job_id, "error": error_message}
        )


class WebhookError(PyhabotAPIException):
    """Exception raised when webhook operations fail."""
    
    def __init__(self, webhook_url: str, error_message: str):
        super().__init__(
            status_code=400,
            detail=f"Webhook error: {error_message}",
            error_code="WEBHOOK_ERROR",
            context={"webhook_url": webhook_url, "error": error_message}
        )


class WebhookTimeoutError(WebhookError):
    """Exception raised when webhook times out."""
    
    def __init__(self, webhook_url: str, timeout: float):
        super().__init__(
            webhook_url,
            f"Webhook request timed out after {timeout} seconds"
        )
        self.error_code = "WEBHOOK_TIMEOUT"
        self.context["timeout"] = timeout


class WebhookRateLimitError(WebhookError):
    """Exception raised when webhook is rate limited."""
    
    def __init__(self, webhook_url: str, retry_after: Optional[int] = None):
        message = "Webhook rate limited"
        if retry_after:
            message += f" - retry after {retry_after} seconds"
        
        super().__init__(webhook_url, message)
        self.error_code = "WEBHOOK_RATE_LIMITED"
        self.context["retry_after"] = retry_after