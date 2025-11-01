"""
Scheduler runner for PYHABOT.

This module implements the background scheduler that manages periodic scraping
of watch URLs with proper jitter, exponential backoff, and graceful shutdown.
"""

import asyncio
import random
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from ..domain.models import Watch
from ..domain.ports import ScraperPort, RepoPort, NotifierPort
from ..domain.services import WatchService, AdvertisementService, NotificationService
from ..logging import get_logger

logger = get_logger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for the scheduler."""
    check_interval: int = 300  # 5 minutes default
    jitter_min: float = 0.8  # 80% of interval
    jitter_max: float = 1.2  # 120% of interval
    max_retries: int = 3
    base_backoff: float = 1.0  # seconds
    max_backoff: float = 60.0  # seconds
    request_delay_min: float = 1.0  # seconds between requests
    request_delay_max: float = 3.0  # seconds between requests


class SchedulerRunner:
    """Background scheduler for scraping watches."""
    
    def __init__(
        self,
        scraper: ScraperPort,
        repo: RepoPort,
        notifier: NotifierPort,
        config: SchedulerConfig,
        webhook_notifier: Optional[NotifierPort] = None
    ):
        """Initialize scheduler runner."""
        self.scraper = scraper
        self.repo = repo
        self.notifier = notifier
        self.webhook_notifier = webhook_notifier
        self.config = config
        
        # Services
        self.watch_service = WatchService(repo)
        self.ad_service = AdvertisementService(repo)
        self.notification_service = NotificationService(notifier, webhook_notifier)
        
        # Runtime state
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._background_task: Optional[asyncio.Task] = None
        self._retry_counts: Dict[int, int] = {}
        
        logger.info("Scheduler runner initialized")
    
    async def start(self) -> None:
        """Start the background scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._shutdown_event.clear()
        self._background_task = asyncio.create_task(self._run_loop())
        logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """Stop the background scheduler gracefully."""
        if not self._running:
            return
        
        logger.info("Stopping scheduler...")
        self._running = False
        self._shutdown_event.set()
        
        if self._background_task:
            try:
                await asyncio.wait_for(self._background_task, timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("Scheduler task did not stop gracefully, cancelling")
                self._background_task.cancel()
                try:
                    await self._background_task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Scheduler stopped")
    
    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        logger.info("Scheduler loop started")
        
        try:
            while self._running:
                try:
                    await self._process_due_watches()
                    
                    # Wait for next cycle or shutdown
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self.config.check_interval
                        )
                        break  # Shutdown requested
                    except asyncio.TimeoutError:
                        continue  # Continue to next cycle
                        
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")
                    # Wait a bit before retrying
                    await asyncio.sleep(10)
                    
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
        finally:
            logger.info("Scheduler loop ended")
    
    async def _process_due_watches(self) -> None:
        """Process all watches that are due for checking."""
        try:
            due_watches = self.watch_service.get_watches_needing_check(
                self.config.check_interval
            )
            
            if not due_watches:
                logger.debug("No watches due for checking")
                return
            
            logger.info(f"Processing {len(due_watches)} due watches")
            
            for watch in due_watches:
                if not self._running:
                    break
                
                try:
                    await self._process_watch(watch)
                    # Reset retry count on success
                    self._retry_counts.pop(watch.id, None)
                    
                    # Random delay between watches
                    delay = random.uniform(
                        self.config.request_delay_min,
                        self.config.request_delay_max
                    )
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    await self._handle_watch_error(watch, e)
                    
        except Exception as e:
            logger.error(f"Error processing due watches: {e}")
    
    async def _process_watch(self, watch: Watch) -> None:
        """Process a single watch."""
        logger.debug(f"Processing watch {watch.id}: {watch.url}")
        
        # Apply jitter to the check
        jitter_delay = self._calculate_jitter_delay()
        if jitter_delay > 0:
            await asyncio.sleep(jitter_delay)
        
        # Scrape the watch URL
        scraped_ads = await self.scraper.scrape_ads(watch.url)
        
        # Process the scraped results
        new_ads, price_changed_ads = self.ad_service.process_scraped_ads(
            watch.id, scraped_ads
        )
        
        # Send notifications for new ads
        if new_ads:
            logger.info(f"Found {len(new_ads)} new ads for watch {watch.id}")
            await self.notification_service.send_new_ad_notifications(watch, new_ads)
        
        # Send notifications for price changes
        if price_changed_ads:
            logger.info(f"Found {len(price_changed_ads)} price changes for watch {watch.id}")
            await self.notification_service.send_price_change_notifications(watch, price_changed_ads)
        
        # Mark the watch as checked
        self.watch_service.mark_watch_checked(watch.id)
        
        logger.debug(f"Completed processing watch {watch.id}")
    
    async def _handle_watch_error(self, watch: Watch, error: Exception) -> None:
        """Handle errors during watch processing."""
        retry_count = self._retry_counts.get(watch.id, 0)
        
        if retry_count >= self.config.max_retries:
            logger.error(f"Max retries exceeded for watch {watch.id}: {error}")
            self._retry_counts.pop(watch.id, None)
            return
        
        # Calculate backoff delay
        backoff_delay = min(
            self.config.base_backoff * (2 ** retry_count),
            self.config.max_backoff
        )
        
        logger.warning(
            f"Error processing watch {watch.id} (attempt {retry_count + 1}/{self.config.max_retries}): {error}. "
            f"Retrying in {backoff_delay:.1f}s"
        )
        
        self._retry_counts[watch.id] = retry_count + 1
        await asyncio.sleep(backoff_delay)
    
    def _calculate_jitter_delay(self) -> float:
        """Calculate random jitter delay."""
        base_interval = self.config.check_interval
        jitter_factor = random.uniform(self.config.jitter_min, self.config.jitter_max)
        return base_interval * (jitter_factor - 1.0)
    
    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running