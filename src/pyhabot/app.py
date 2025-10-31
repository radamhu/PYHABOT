"""
Main application class for PYHABOT.

This module contains the core Pyhabot class that orchestrates the bot's
functionality including background scraping, notifications, and integration management.
"""

import asyncio
from typing import Optional

from .config import Config
from .logging import get_logger
from .scheduler import SchedulerRunner, SchedulerConfig

logger = get_logger(__name__)


class Pyhabot:
    """Main application class for PYHABOT."""
    
    def __init__(self, config: Config):
        """Initialize the bot with configuration."""
        self.config = config
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Initialize components (will be set up when running)
        self.scheduler: Optional[SchedulerRunner] = None
        self.integration = None
        self.scraper = None
        self.repo = None
        
        logger.info("PYHABOT initialized")
    
    async def run_async(self, integration: str) -> None:
        """Run the bot asynchronously with the specified integration."""
        logger.info(f"Starting PYHABOT with {integration} integration")
        self._running = True
        
        try:
            # Initialize components
            self.integration = await self._create_integration(integration)
            self.scraper = await self._create_scraper()
            self.repo = self._create_repo()
            
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
                notifier=self.integration,
                config=scheduler_config
            )
            
            await self.scheduler.start()
            
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
            logger.info("PYHABOT stopped")
    
    def run(self, integration: str) -> int:
        """Run the bot synchronously with the specified integration."""
        try:
            # Check if we're already in an event loop
            try:
                asyncio.get_running_loop()
                # If we're here, we're in a running loop
                # Create a new event loop in a thread to run the coroutine
                import threading
                import queue
                
                result_queue = queue.Queue()
                exception_queue = queue.Queue()
                
                def run_in_thread():
                    try:
                        asyncio.run(self.run_async(integration))
                        result_queue.put(0)
                    except Exception as e:
                        exception_queue.put(e)
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()
                
                # Check for exceptions
                if not exception_queue.empty():
                    raise exception_queue.get()
                
                return result_queue.get()
                
            except RuntimeError:
                # No running loop, we can use asyncio.run normally
                asyncio.run(self.run_async(integration))
                return 0
        except Exception as e:
            logger.error(f"Failed to run bot: {e}")
            return 1
    
    async def shutdown(self) -> None:
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
        
        if self.integration:
            await self.integration.cleanup()
            self.integration = None
        
        if self.scraper:
            # Close the aiohttp session
            if hasattr(self.scraper, 'session'):
                await self.scraper.session.close()
            self.scraper = None
        
        self.repo = None
    
    async def _create_integration(self, integration_name: str):
        """Create and initialize the integration."""
        # Import here to avoid circular imports
        from .adapters.integrations import create_integration
        
        integration = await create_integration(integration_name, self.config)
        # Note: initialize() method doesn't exist yet, but we'll call cleanup() later
        return integration
    
    async def _create_scraper(self):
        """Create scraper adapter."""
        import aiohttp
        from .adapters.scraping.hardverapro import HardveraproScraper
        
        session = aiohttp.ClientSession()
        return HardveraproScraper(session, self.config.user_agents)
    
    def _create_repo(self):
        """Create repository adapter."""
        from .adapters.repos.tinydb_repo import TinyDBRepository
        return TinyDBRepository(self.config.persistent_data_path)
    
    @property
    def is_running(self) -> bool:
        """Check if the bot is currently running."""
        return self._running