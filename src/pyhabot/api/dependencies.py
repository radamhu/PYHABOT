"""
Dependency injection for PYHABOT API.

This module provides FastAPI dependency functions for injecting
services and other components into API endpoints.
"""

import os
from typing import AsyncGenerator, Optional

from ..simple_config import SimpleConfig as Config
from ..adapters.repos.tinydb_repo import TinyDBRepository
from ..domain.services import WatchService, AdvertisementService, NotificationService
from ..adapters.scraping.hardverapro import HardveraproScraper
from ..adapters.notifications.webhook import WebhookNotifier
from .job_manager import get_job_queue
from .exceptions import ServiceUnavailableError

# Global instances for dependency injection
_config: Optional[Config] = None
_repo: Optional[TinyDBRepository] = None
_watch_service: Optional[WatchService] = None
_ad_service: Optional[AdvertisementService] = None
_scraper: Optional[HardveraproScraper] = None
_webhook_notifier: Optional[WebhookNotifier] = None
_notification_service: Optional[NotificationService] = None


async def get_config() -> Config:
    """Get application configuration."""
    global _config
    if _config is None:
        _config = Config()
    return _config


async def get_repo() -> TinyDBRepository:
    """Get repository instance."""
    global _repo
    if _repo is None:
        config = await get_config()
        try:
            _repo = TinyDBRepository(config.persistent_data_path)
        except Exception as e:
            raise ServiceUnavailableError("database")
    return _repo


async def get_watch_service() -> WatchService:
    """Get watch service instance."""
    global _watch_service
    if _watch_service is None:
        repo = await get_repo()
        _watch_service = WatchService(repo)
    return _watch_service


async def get_advertisement_service() -> AdvertisementService:
    """Get advertisement service instance."""
    global _ad_service
    if _ad_service is None:
        repo = await get_repo()
        _ad_service = AdvertisementService(repo)
    return _ad_service


async def get_scraper() -> HardveraproScraper:
    """Get scraper instance."""
    global _scraper
    if _scraper is None:
        # We'll need to create an aiohttp session for the scraper
        # For now, create a placeholder
        import aiohttp
        async with aiohttp.ClientSession() as session:
            _scraper = HardveraproScraper(session)
    return _scraper


async def get_webhook_notifier() -> WebhookNotifier:
    """Get webhook notifier instance."""
    global _webhook_notifier
    if _webhook_notifier is None:
        import aiohttp
        session = aiohttp.ClientSession()
        _webhook_notifier = WebhookNotifier(session)
    return _webhook_notifier


async def get_notification_service() -> NotificationService:
    """Get notification service instance."""
    global _notification_service
    if _notification_service is None:
        webhook_notifier = await get_webhook_notifier()
        # For now, we'll use the webhook notifier as the main notifier
        # In a full implementation, we would have multiple notifiers
        _notification_service = NotificationService(
            notifier=webhook_notifier,
            webhook_notifier=webhook_notifier
        )
    return _notification_service


async def cleanup_dependencies():
    """Cleanup global dependencies."""
    global _config, _repo, _watch_service, _ad_service, _scraper, _webhook_notifier, _notification_service
    
    # Close any open connections or resources
    if _scraper and hasattr(_scraper, 'session'):
        await _scraper.session.close()
    
    if _webhook_notifier and hasattr(_webhook_notifier, 'session'):
        await _webhook_notifier.session.close()
    
    # Reset global instances
    _config = None
    _repo = None
    _watch_service = None
    _ad_service = None
    _scraper = None
    _webhook_notifier = None
    _notification_service = None