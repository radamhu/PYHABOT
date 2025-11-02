"""
Watch management API endpoints.

This module provides RESTful endpoints for managing watches,
including CRUD operations and webhook configuration.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from ...api.dependencies import get_watch_service, get_advertisement_service
from ...api.models import (
    WatchResponse, 
    CreateWatchRequest, 
    SetWebhookRequest,
    AdvertisementResponse,
    watch_to_response,
    advertisement_to_response
)
from ...api.exceptions import (
    WatchNotFoundError,
    AdvertisementNotFoundError,
    InvalidURLError,
    DuplicateWatchError
)

router = APIRouter(prefix="/api/v1/watches", tags=["watches"])


@router.post(
    "/",
    response_model=WatchResponse,
    status_code=201,
    summary="Create a new watch",
    description="Add a new URL to monitor for HardverApró advertisements. The system will periodically check this URL and notify you of new ads.",
    responses={
        201: {"description": "Watch created successfully"},
        400: {"description": "Invalid URL or validation error"},
        409: {"description": "Watch already exists for this URL"},
        422: {"description": "Validation error"}
    }
)
async def create_watch(
    request: CreateWatchRequest,
    watch_service = Depends(get_watch_service)
) -> WatchResponse:
    """Create a new watch for monitoring HardverApró search results."""
    try:
        # Check if watch already exists for this URL
        existing_watches = watch_service.get_all_watches()
        for existing_watch in existing_watches:
            if existing_watch.url == str(request.url):
                raise DuplicateWatchError(str(request.url))
        
        # Create new watch
        watch_id = watch_service.create_watch(str(request.url))
        
        # Set webhook if provided
        if request.webhook_url:
            watch_service.set_webhook(watch_id, str(request.webhook_url))
        
        # Get the created watch
        watch = watch_service.get_watch(watch_id)
        if not watch:
            raise HTTPException(status_code=500, detail="Failed to create watch")
        
        return watch_to_response(watch)
        
    except DuplicateWatchError:
        raise
    except ValueError as e:
        if "Invalid URL" in str(e):
            raise InvalidURLError(str(request.url), str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/",
    response_model=List[WatchResponse],
    summary="List all watches",
    description="Retrieve all configured watches with their current status and settings.",
    responses={
        200: {"description": "List of watches retrieved successfully"}
    }
)
async def list_watches(
    watch_service = Depends(get_watch_service)
) -> List[WatchResponse]:
    """List all configured watches."""
    try:
        watches = watch_service.get_all_watches()
        return [watch_to_response(watch) for watch in watches]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{watch_id}",
    response_model=WatchResponse,
    summary="Get a specific watch",
    description="Retrieve detailed information about a specific watch by its ID.",
    responses={
        200: {"description": "Watch retrieved successfully"},
        404: {"description": "Watch not found"}
    }
)
async def get_watch(
    watch_id: int,
    watch_service = Depends(get_watch_service)
) -> WatchResponse:
    """Get a specific watch by ID."""
    try:
        watch = watch_service.get_watch(watch_id)
        if not watch:
            raise WatchNotFoundError(watch_id)
        
        return watch_to_response(watch)
        
    except WatchNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{watch_id}",
    summary="Delete a watch",
    description="Remove a watch and all its associated advertisements from the system.",
    responses={
        204: {"description": "Watch deleted successfully"},
        404: {"description": "Watch not found"}
    }
)
async def delete_watch(
    watch_id: int,
    watch_service = Depends(get_watch_service)
):
    """Delete a watch by ID."""
    try:
        success = watch_service.remove_watch(watch_id)
        if not success:
            raise WatchNotFoundError(watch_id)
        
        return None  # FastAPI will return 204 No Content
        
    except WatchNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put(
    "/{watch_id}/webhook",
    response_model=WatchResponse,
    summary="Set webhook URL",
    description="Configure a webhook URL for receiving notifications about new advertisements for this watch. Supports Discord, Slack, and generic webhooks.",
    responses={
        200: {"description": "Webhook URL updated successfully"},
        404: {"description": "Watch not found"},
        422: {"description": "Invalid webhook URL or configuration"}
    }
)
async def set_webhook(
    watch_id: int,
    request: SetWebhookRequest,
    watch_service = Depends(get_watch_service)
) -> WatchResponse:
    """Set webhook URL for a watch with enhanced configuration."""
    try:
        # Verify watch exists
        watch = watch_service.get_watch(watch_id)
        if not watch:
            raise WatchNotFoundError(watch_id)
        
        # Set webhook URL (basic implementation - in future, store enhanced config)
        success = watch_service.set_webhook(watch_id, str(request.webhook_url))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set webhook URL")
        
        # TODO: Store enhanced webhook configuration (type, username, avatar, headers)
        # This would require extending the Watch model and repository
        
        # Get updated watch
        updated_watch = watch_service.get_watch(watch_id)
        return watch_to_response(updated_watch)
        
    except WatchNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{watch_id}/webhook",
    response_model=WatchResponse,
    summary="Remove webhook URL",
    description="Remove the webhook URL configuration for this watch. Notifications will be disabled.",
    responses={
        200: {"description": "Webhook URL removed successfully"},
        404: {"description": "Watch not found"}
    }
)
async def remove_webhook(
    watch_id: int,
    watch_service = Depends(get_watch_service)
) -> WatchResponse:
    """Remove webhook URL from a watch."""
    try:
        # Verify watch exists
        watch = watch_service.get_watch(watch_id)
        if not watch:
            raise WatchNotFoundError(watch_id)
        
        # Clear webhook
        success = watch_service.clear_webhook(watch_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove webhook URL")
        
        # Get updated watch
        updated_watch = watch_service.get_watch(watch_id)
        return watch_to_response(updated_watch)
        
    except WatchNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{watch_id}/ads",
    response_model=List[AdvertisementResponse],
    summary="Get advertisements for a watch",
    description="Retrieve all active advertisements found by this watch, with optional filtering.",
    responses={
        200: {"description": "Advertisements retrieved successfully"},
        404: {"description": "Watch not found"}
    }
)
async def get_watch_ads(
    watch_id: int,
    active_only: bool = Query(True, description="Filter to only active advertisements"),
    ad_service = Depends(get_advertisement_service),
    watch_service = Depends(get_watch_service)
) -> List[AdvertisementResponse]:
    """Get advertisements for a specific watch."""
    try:
        # Verify watch exists
        watch = watch_service.get_watch(watch_id)
        if not watch:
            raise WatchNotFoundError(watch_id)
        
        # Get advertisements
        if active_only:
            ads = ad_service.get_active_ads_for_watch(watch_id)
        else:
            # Get all ads for watch (would need to implement this in service)
            ads = ad_service.get_active_ads_for_watch(watch_id)  # Placeholder
        
        return [advertisement_to_response(ad) for ad in ads]
        
    except WatchNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")