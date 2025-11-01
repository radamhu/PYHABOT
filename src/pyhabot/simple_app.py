"""
Simplified main application class for PYHABOT.

This module provides a streamlined version without the integration pattern,
running as a straightforward async Python application.
"""

import asyncio
import aiohttp
from typing import Optional, List
from datetime import datetime

from .simple_config import SimpleConfig as Config
from .logging import get_logger
from .scheduler import SchedulerRunner, SchedulerConfig
from .adapters.scraping.hardverapro import HardveraproScraper
from .adapters.repos.tinydb_repo import TinyDBRepository
from .adapters.notifications.webhook import WebhookNotifier
from .domain.services import WatchService

logger = get_logger(__name__)


class SimplePyhabot:
    """Simplified PYHABOT application without integration pattern."""
    
    def __init__(self, config: Config):
        """Initialize the bot with configuration."""
        self.config = config
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Initialize components (will be set up when running)
        self.scheduler: Optional[SchedulerRunner] = None
        self.webhook_notifier: Optional[WebhookNotifier] = None
        self.scraper: Optional[HardveraproScraper] = None
        self.repo: Optional[TinyDBRepository] = None
        self.watch_service: Optional[WatchService] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Simple PYHABOT initialized")
    
    async def start(self) -> None:
        """Start the bot asynchronously."""
        logger.info("Starting Simple PYHABOT")
        self._running = True
        
        try:
            # Create shared aiohttp session
            self.session = aiohttp.ClientSession()
            
            # Initialize components
            self.scraper = HardveraproScraper(self.session, self.config.user_agents)
            self.repo = TinyDBRepository(self.config.persistent_data_path)
            self.webhook_notifier = WebhookNotifier(self.session)
            self.watch_service = WatchService(self.repo)
            
            # Initialize and start scheduler
            scheduler_config = SchedulerConfig(
                check_interval=self.config.scrape_interval,
                jitter_min=0.8,  # 80% of interval
                jitter_max=1.2,  # 120% of interval
                max_retries=self.config.max_retries,
                base_backoff=1.0,  # seconds
                max_backoff=60.0,  # seconds
                request_delay_min=1.0,  # seconds between requests
                request_delay_max=3.0  # seconds between requests
            )
            
            self.scheduler = SchedulerRunner(
                scraper=self.scraper,
                repo=self.repo,
                notifier=self,  # Use self as notifier for simple console output
                config=scheduler_config,
                webhook_notifier=self.webhook_notifier
            )
            
            await self.scheduler.start()
            logger.info("Simple PYHABOT started successfully")
            
            # Keep running until shutdown is requested
            await self._shutdown_event.wait()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
        finally:
            await self._cleanup()
            self._running = False
            logger.info("Simple PYHABOT stopped")
    
    async def stop(self) -> None:
        """Gracefully shutdown the bot."""
        logger.info("Initiating graceful shutdown")
        self._shutdown_event.set()
        await self._cleanup()
        logger.info("Shutdown complete")
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.scheduler:
            await self.scheduler.stop()
            self.scheduler = None
        
        if self.session:
            await self.session.close()
            self.session = None
        
        self.webhook_notifier = None
        self.scraper = None
        self.repo = None
        self.watch_service = None
    
    # Simple notification methods (replacing integration pattern)
    async def send_message_to_channel(
        self, 
        channel_id: str, 
        text: str, 
        no_preview: bool = False, 
        **kwargs
    ) -> bool:
        """Send a message to console (simplified notification)."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] PYHABOT Notification:")
            print(f"{text}")
            print("-" * 50)
            return True
        except Exception as e:
            logger.error(f"Failed to send console message: {e}")
            return False
    
    def format_message(self, message_type: str, **kwargs) -> str:
        """Format message for console display."""
        if message_type == "new_ad":
            return (
                f"🆕 NEW AD DETECTED\n"
                f"Title: {kwargs.get('title', 'N/A')}\n"
                f"Price: {kwargs.get('price', 'N/A')} Ft\n"
                f"Location: {kwargs.get('city', 'N/A')}\n"
                f"URL: {kwargs.get('url', 'N/A')}"
            )
        elif message_type == "price_change":
            return (
                f"💰 PRICE CHANGE DETECTED\n"
                f"Title: {kwargs.get('title', 'N/A')}\n"
                f"Old Price: {kwargs.get('old_price', 'N/A')} Ft\n"
                f"New Price: {kwargs.get('new_price', 'N/A')} Ft\n"
                f"URL: {kwargs.get('url', 'N/A')}"
            )
        else:
            return str(kwargs.get('text', ''))
    
    # Watch management methods
    async def add_watch(self, url: str) -> int:
        """Add a new watch URL."""
        try:
            # Initialize minimal services needed for this operation
            if not self.repo:
                from .adapters.repos.tinydb_repo import TinyDBRepository
                self.repo = TinyDBRepository(self.config.persistent_data_path)
            if not self.watch_service:
                self.watch_service = WatchService(self.repo)
            
            watch_id = self.watch_service.create_watch(url)
            print(f"✅ Watch added successfully with ID: {watch_id}")
            return watch_id
        except Exception as e:
            logger.error(f"Failed to add watch: {e}")
            print(f"❌ Failed to add watch: {e}")
            raise
    
    async def list_watches(self) -> List[dict]:
        """List all watches."""
        try:
            # Initialize minimal services needed for this operation
            if not self.repo:
                from .adapters.repos.tinydb_repo import TinyDBRepository
                self.repo = TinyDBRepository(self.config.persistent_data_path)
            if not self.watch_service:
                self.watch_service = WatchService(self.repo)
            
            watches = self.watch_service.get_all_watches()
            if not watches:
                print("📋 No watches configured.")
                return []
            
            print("📋 Active watches:")
            watch_dicts = []
            for watch in watches:
                status = "🟢 Webhook" if watch.webhook else "🔵 Console only"
                print(f"  ID {watch.id}: {watch.url} [{status}]")
                watch_dicts.append({
                    'id': watch.id,
                    'url': watch.url,
                    'webhook': watch.webhook
                })
            
            return watch_dicts
        except Exception as e:
            logger.error(f"Failed to list watches: {e}")
            print(f"❌ Failed to list watches: {e}")
            raise
    
    async def remove_watch(self, watch_id: int) -> bool:
        """Remove a watch by ID."""
        try:
            # Initialize minimal services needed for this operation
            if not self.repo:
                from .adapters.repos.tinydb_repo import TinyDBRepository
                self.repo = TinyDBRepository(self.config.persistent_data_path)
            if not self.watch_service:
                self.watch_service = WatchService(self.repo)
            
            success = self.watch_service.remove_watch(watch_id)
            if success:
                print(f"✅ Watch {watch_id} removed successfully")
            else:
                print(f"❌ Watch {watch_id} not found")
            return success
        except Exception as e:
            logger.error(f"Failed to remove watch: {e}")
            print(f"❌ Failed to remove watch: {e}")
            raise
    
    async def set_webhook(self, watch_id: int, webhook_url: str) -> bool:
        """Set webhook for a watch."""
        try:
            # Initialize minimal services needed for this operation
            if not self.repo:
                from .adapters.repos.tinydb_repo import TinyDBRepository
                self.repo = TinyDBRepository(self.config.persistent_data_path)
            if not self.watch_service:
                self.watch_service = WatchService(self.repo)
            
            watch = self.watch_service.get_watch(watch_id)
            if not watch:
                print(f"❌ Watch {watch_id} not found")
                return False
            
            # Update watch with webhook
            watch.webhook = webhook_url
            self.repo.update_watch(watch)
            
            print(f"✅ Webhook set for watch {watch_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            print(f"❌ Failed to set webhook: {e}")
            raise
    
    async def force_rescrape(self, watch_id: int) -> bool:
        """Force re-scraping for a specific watch."""
        try:
            # Initialize minimal services needed for this operation
            if not self.repo:
                from .adapters.repos.tinydb_repo import TinyDBRepository
                self.repo = TinyDBRepository(self.config.persistent_data_path)
            if not self.watch_service:
                self.watch_service = WatchService(self.repo)
            
            watch = self.watch_service.get_watch(watch_id)
            if not watch:
                print(f"❌ Watch {watch_id} not found")
                return False
            
            # Clear existing ads for this watch
            self.repo.clear_advertisements_for_watch(watch_id)
            
            # Reset last_checked to force scraping
            watch.last_checked = 0.0
            self.repo.update_watch(watch)
            
            print(f"✅ Force re-scrape initiated for watch {watch_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to force rescrape: {e}")
            print(f"❌ Failed to force rescrape: {e}")
            raise
    
    @property
    def is_running(self) -> bool:
        """Check if the bot is currently running."""
        return self._running