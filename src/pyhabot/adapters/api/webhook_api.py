"""
Webhook management API endpoints.

This module provides endpoints for webhook configuration, testing,
and management including advanced webhook features.
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from aiohttp import ClientSession

from ...api.dependencies import get_watch_service, get_notification_service
from ...api.models import (
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookConfigResponse,
    ErrorResponse
)
from ...api.exceptions import WatchNotFoundError, WebhookError
from ...adapters.notifications.webhook import WebhookNotifier

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post(
    "/test",
    response_model=WebhookTestResponse,
    summary="Test webhook functionality",
    description="Send a test notification to a webhook URL to verify connectivity and configuration.",
    responses={
        200: {"description": "Webhook test completed"},
        400: {"description": "Invalid webhook configuration"},
        422: {"description": "Validation error"}
    }
)
async def test_webhook(
    request: WebhookTestRequest,
    notification_service = Depends(get_notification_service)
) -> WebhookTestResponse:
    """Test a webhook configuration by sending a test notification."""
    start_time = time.time()
    
    try:
        # Create a temporary webhook notifier for testing
        # We'll use the notification service's session if available
        session = getattr(notification_service.webhook_notifier, 'session', None)
        if not session:
            # Create a temporary session for testing
            async with ClientSession() as temp_session:
                webhook_notifier = WebhookNotifier(temp_session)
                return await _perform_webhook_test(
                    webhook_notifier, request, start_time
                )
        else:
            webhook_notifier = WebhookNotifier(session)
            return await _perform_webhook_test(
                webhook_notifier, request, start_time
            )
            
    except Exception as e:
        total_time = time.time() - start_time
        return WebhookTestResponse(
            success=False,
            response_status=None,
            response_body=None,
            error_message=str(e),
            attempts=1,
            total_time=total_time
        )


async def _perform_webhook_test(
    webhook_notifier: WebhookNotifier,
    request: WebhookTestRequest,
    start_time: float
) -> WebhookTestResponse:
    """Perform the actual webhook test."""
    # Prepare webhook options
    webhook_options = {
        "webhook_type": request.webhook_type,
        "username": request.webhook_username,
        "avatar_url": request.webhook_avatar,
        "headers": request.custom_headers or {}
    }
    
    # Send test notification
    test_message = request.test_message or "Test message from PYHABOT"
    success = await webhook_notifier.send_webhook_notification(
        str(request.webhook_url),
        test_message,
        **webhook_options
    )
    
    total_time = time.time() - start_time
    
    if success:
        return WebhookTestResponse(
            success=True,
            response_status=200,  # We don't get the actual status from the notifier
            response_body="Test notification sent successfully",
            error_message=None,
            attempts=1,
            total_time=total_time
        )
    else:
        return WebhookTestResponse(
            success=False,
            response_status=None,
            response_body=None,
            error_message="Webhook notification failed",
            attempts=1,
            total_time=total_time
        )


@router.get(
    "/watches/{watch_id}/config",
    response_model=WebhookConfigResponse,
    summary="Get webhook configuration for a watch",
    description="Retrieve the current webhook configuration and statistics for a specific watch.",
    responses={
        200: {"description": "Webhook configuration retrieved"},
        404: {"description": "Watch not found"}
    }
)
async def get_webhook_config(
    watch_id: int,
    watch_service = Depends(get_watch_service)
) -> WebhookConfigResponse:
    """Get webhook configuration for a specific watch."""
    try:
        watch = watch_service.get_watch(watch_id)
        if not watch:
            raise WatchNotFoundError(watch_id)
        
        # For now, return basic config. In a full implementation,
        # we would store and retrieve additional webhook metadata
        return WebhookConfigResponse(
            watch_id=watch_id,
            webhook_url=watch.webhook,
            webhook_type="generic",  # Default, would be stored in enhanced model
            webhook_username=None,
            webhook_avatar=None,
            custom_headers=None,
            last_notification=None,  # Would be tracked in enhanced implementation
            notification_count=0,    # Would be tracked in enhanced implementation
            failed_notifications=0  # Would be tracked in enhanced implementation
        )
        
    except WatchNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/watches/{watch_id}/test",
    response_model=WebhookTestResponse,
    summary="Test webhook for a watch",
    description="Send a test notification using the webhook configuration of a specific watch.",
    responses={
        200: {"description": "Webhook test completed"},
        404: {"description": "Watch not found"},
        400: {"description": "No webhook configured for watch"}
    }
)
async def test_watch_webhook(
    watch_id: int,
    test_message: str = "Test notification from PYHABOT",
    watch_service = Depends(get_watch_service),
    notification_service = Depends(get_notification_service)
) -> WebhookTestResponse:
    """Test the webhook configuration of a specific watch."""
    try:
        watch = watch_service.get_watch(watch_id)
        if not watch:
            raise WatchNotFoundError(watch_id)
        
        if not watch.webhook:
            raise HTTPException(
                status_code=400, 
                detail="No webhook configured for this watch"
            )
        
        start_time = time.time()
        
        # Send test notification using the watch's webhook
        success = await notification_service.webhook_notifier.send_webhook_notification(
            watch.webhook,
            test_message
        )
        
        total_time = time.time() - start_time
        
        return WebhookTestResponse(
            success=success,
            response_status=200 if success else None,
            response_body="Test notification sent successfully" if success else None,
            error_message=None if success else "Webhook notification failed",
            attempts=1,
            total_time=total_time
        )
        
    except WatchNotFoundError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/types",
    summary="Get supported webhook types",
    description="Retrieve a list of supported webhook types and their configuration options.",
    responses={
        200: {"description": "Supported webhook types retrieved"}
    }
)
async def get_webhook_types() -> Dict[str, Any]:
    """Get information about supported webhook types."""
    return {
        "webhook_types": {
            "discord": {
                "name": "Discord",
                "description": "Discord webhook with embed support",
                "features": ["embeds", "custom_username", "custom_avatar", "tts"],
                "payload_format": "discord_webhook",
                "documentation": "https://discord.com/developers/docs/resources/webhook"
            },
            "slack": {
                "name": "Slack",
                "description": "Slack incoming webhook",
                "features": ["attachments", "custom_username", "custom_icon"],
                "payload_format": "slack_webhook",
                "documentation": "https://api.slack.com/messaging/webhooks"
            },
            "generic": {
                "name": "Generic",
                "description": "Generic HTTP webhook with JSON payload",
                "features": ["custom_headers", "custom_payload"],
                "payload_format": "json",
                "documentation": None
            }
        },
        "default_type": "generic",
        "retry_policy": {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "backoff_factor": 2.0,
            "jitter": True
        }
    }