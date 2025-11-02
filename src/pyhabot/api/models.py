"""
Pydantic models for PYHABOT API requests and responses.

This module defines the data models used for API validation,
serialization, and automatic OpenAPI documentation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator

from ..domain.models import Watch, Advertisement


class WatchResponse(BaseModel):
    """Watch model for API responses."""
    id: int = Field(..., description="Unique identifier for the watch")
    url: HttpUrl = Field(..., description="URL being monitored")
    last_checked: float = Field(..., description="Timestamp of last check (Unix epoch)")
    webhook: Optional[HttpUrl] = Field(None, description="Webhook URL for notifications")
    active: bool = Field(True, description="Whether the watch is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "url": "https://hardverapro.hu/search?param=value",
                "last_checked": 1698765432.0,
                "webhook": "https://discord.com/api/webhooks/123/abc",
                "active": True
            }
        }


class CreateWatchRequest(BaseModel):
    """Request model for creating a new watch."""
    url: HttpUrl = Field(..., description="URL to monitor for HardverApró advertisements")
    webhook_url: Optional[HttpUrl] = Field(None, description="Optional webhook URL for notifications")
    
    @validator('url')
    def validate_hardverapro_url(cls, v):
        """Validate that URL is a valid HardverApró URL."""
        v_str = str(v)
        if "hardverapro.hu" not in v_str:
            raise ValueError("URL must be a valid HardverApró URL")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://hardverapro.hu/search?param=value",
                "webhook_url": "https://discord.com/api/webhooks/123/abc"
            }
        }


class SetWebhookRequest(BaseModel):
    """Request model for setting webhook URL."""
    webhook_url: HttpUrl = Field(..., description="Webhook URL for notifications")
    webhook_type: Optional[str] = Field("generic", description="Type of webhook (discord, slack, generic)")
    webhook_username: Optional[str] = Field(None, description="Username for webhook posts")
    webhook_avatar: Optional[HttpUrl] = Field(None, description="Avatar URL for webhook posts")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom headers for webhook requests")
    
    @validator('webhook_type')
    def validate_webhook_type(cls, v):
        """Validate webhook type."""
        allowed_types = ['discord', 'slack', 'generic']
        if v and v not in allowed_types:
            raise ValueError(f"webhook_type must be one of: {', '.join(allowed_types)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "webhook_url": "https://discord.com/api/webhooks/123/abc",
                "webhook_type": "discord",
                "webhook_username": "PYHABOT",
                "webhook_avatar": "https://example.com/avatar.png",
                "custom_headers": {
                    "Authorization": "Bearer token123"
                }
            }
        }


class WebhookTestRequest(BaseModel):
    """Request model for testing webhook functionality."""
    webhook_url: HttpUrl = Field(..., description="Webhook URL to test")
    webhook_type: Optional[str] = Field("generic", description="Type of webhook (discord, slack, generic)")
    webhook_username: Optional[str] = Field(None, description="Username for webhook posts")
    webhook_avatar: Optional[HttpUrl] = Field(None, description="Avatar URL for webhook posts")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom headers for webhook requests")
    test_message: Optional[str] = Field("Test message from PYHABOT", description="Custom test message")
    
    @validator('webhook_type')
    def validate_webhook_type(cls, v):
        """Validate webhook type."""
        allowed_types = ['discord', 'slack', 'generic']
        if v and v not in allowed_types:
            raise ValueError(f"webhook_type must be one of: {', '.join(allowed_types)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "webhook_url": "https://discord.com/api/webhooks/123/abc",
                "webhook_type": "discord",
                "webhook_username": "PYHABOT",
                "test_message": "This is a test notification from PYHABOT"
            }
        }


class WebhookTestResponse(BaseModel):
    """Response model for webhook test results."""
    success: bool = Field(..., description="Whether the webhook test was successful")
    response_status: Optional[int] = Field(None, description="HTTP status code from webhook")
    response_body: Optional[str] = Field(None, description="Response body from webhook")
    error_message: Optional[str] = Field(None, description="Error message if test failed")
    attempts: int = Field(..., description="Number of attempts made")
    total_time: float = Field(..., description="Total time taken in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response_status": 204,
                "response_body": "",
                "error_message": None,
                "attempts": 1,
                "total_time": 0.234
            }
        }


class WebhookConfigResponse(BaseModel):
    """Response model for webhook configuration."""
    watch_id: int = Field(..., description="Watch ID")
    webhook_url: Optional[HttpUrl] = Field(None, description="Configured webhook URL")
    webhook_type: Optional[str] = Field(None, description="Configured webhook type")
    webhook_username: Optional[str] = Field(None, description="Configured webhook username")
    webhook_avatar: Optional[HttpUrl] = Field(None, description="Configured webhook avatar URL")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Configured custom headers")
    last_notification: Optional[datetime] = Field(None, description="Timestamp of last successful notification")
    notification_count: int = Field(0, description="Total number of notifications sent")
    failed_notifications: int = Field(0, description="Number of failed notifications")
    
    class Config:
        json_schema_extra = {
            "example": {
                "watch_id": 1,
                "webhook_url": "https://discord.com/api/webhooks/123/abc",
                "webhook_type": "discord",
                "webhook_username": "PYHABOT",
                "webhook_avatar": "https://example.com/avatar.png",
                "custom_headers": {
                    "Authorization": "Bearer token123"
                },
                "last_notification": "2025-11-02T13:33:00Z",
                "notification_count": 15,
                "failed_notifications": 2
            }
        }


class AdvertisementResponse(BaseModel):
    """Advertisement model for API responses."""
    id: int = Field(..., description="Advertisement ID from HardverApró")
    title: str = Field(..., description="Advertisement title")
    url: HttpUrl = Field(..., description="Advertisement URL")
    price: Optional[int] = Field(None, description="Price in HUF (None if not specified)")
    city: str = Field(..., description="Location of the item")
    date: str = Field(..., description="Publication date")
    pinned: bool = Field(..., description="Whether the advertisement is pinned")
    seller_name: str = Field(..., description="Name of the seller")
    seller_url: HttpUrl = Field(..., description="Seller profile URL")
    seller_rates: str = Field(..., description="Seller rating")
    image: Optional[str] = Field(None, description="Image URL if available")
    watch_id: int = Field(..., description="ID of the watch that found this ad")
    active: bool = Field(True, description="Whether the advertisement is still active")
    prev_prices: List[int] = Field(default_factory=list, description="Previous prices for price tracking")
    price_alert: bool = Field(False, description="Whether price alerts are enabled")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123456789,
                "title": "Eladó használt laptop",
                "url": "https://hardverapro.hu/termek/123456789",
                "price": 150000,
                "city": "Budapest",
                "date": "2025-11-02",
                "pinned": False,
                "seller_name": "János",
                "seller_url": "https://hardverapro.hu/profil/janos",
                "seller_rates": "100% (25)",
                "image": "https://hardverapro.hu/kepek/123456789.jpg",
                "watch_id": 1,
                "active": True,
                "prev_prices": [160000, 155000],
                "price_alert": True
            }
        }


class JobStatus(str, Enum):
    """Job status enumeration for API responses."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    """Job status response model."""
    id: str = Field(..., description="Unique job identifier")
    type: str = Field(..., description="Type of job being executed")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error: Optional[str] = Field(None, description="Error message if job failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "rescrape",
                "status": "completed",
                "created_at": "2025-11-02T13:33:00Z",
                "started_at": "2025-11-02T13:33:01Z",
                "completed_at": "2025-11-02T13:33:45Z",
                "result": {
                    "watch_id": 1,
                    "new_ads": 3,
                    "updated_ads": 1,
                    "processing_time": 44.2
                },
                "error": None
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Watch not found",
                "error_code": "WATCH_NOT_FOUND",
                "details": {
                    "watch_id": 999
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Health check timestamp")
    services: Dict[str, str] = Field(..., description="Status of individual services")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-11-02T13:33:00Z",
                "services": {
                    "database": "healthy",
                    "scraper": "healthy",
                    "scheduler": "healthy",
                    "job_queue": "healthy"
                }
            }
        }


# Helper functions to convert domain models to API models
def watch_to_response(watch: Watch) -> WatchResponse:
    """Convert domain Watch to API response model."""
    return WatchResponse(
        id=watch.id,
        url=watch.url,
        last_checked=watch.last_checked,
        webhook=watch.webhook,
        active=True  # Assume active if it exists
    )


def advertisement_to_response(ad: Advertisement) -> AdvertisementResponse:
    """Convert domain Advertisement to API response model."""
    return AdvertisementResponse(
        id=ad.id,
        title=ad.title,
        url=ad.url,
        price=ad.price,
        city=ad.city,
        date=ad.date,
        pinned=ad.pinned,
        seller_name=ad.seller_name,
        seller_url=ad.seller_url,
        seller_rates=ad.seller_rates,
        image=ad.image,
        watch_id=ad.watch_id,
        active=ad.active,
        prev_prices=ad.prev_prices,
        price_alert=ad.price_alert
    )