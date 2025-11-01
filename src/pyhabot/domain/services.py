"""
Domain services for PYHABOT.

These services contain the core business logic and use cases, coordinating
between domain models and ports to implement the application's functionality.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .models import Watch, Advertisement, NotificationTarget, NotificationType
from .ports import ScraperPort, RepoPort, NotifierPort

logger = logging.getLogger(__name__)


class WatchService:
    """Service for managing watch configurations."""
    
    def __init__(self, repo: RepoPort):
        self.repo = repo
    
    def create_watch(self, url: str) -> int:
        """Create a new watch for the given URL."""
        watch_id = self.repo.add_watch(url)
        logger.info(f"Created new watch {watch_id} for URL: {url}")
        return watch_id
    
    def get_watch(self, watch_id: int) -> Optional[Watch]:
        """Get a watch by ID."""
        return self.repo.get_watch(watch_id)
    
    def get_all_watches(self) -> List[Watch]:
        """Get all watches."""
        return self.repo.get_all_watches()
    
    def remove_watch(self, watch_id: int) -> bool:
        """Remove a watch and its associated advertisements."""
        watch = self.repo.get_watch(watch_id)
        if not watch:
            logger.warning(f"Attempted to remove non-existent watch {watch_id}")
            return False
        
        success = self.repo.remove_watch(watch_id)
        if success:
            logger.info(f"Removed watch {watch_id}")
        return success
    
    def set_notification_target(self, watch_id: int, channel_id: str, integration: str) -> bool:
        """Set the notification target for a watch."""
        watch = self.repo.get_watch(watch_id)
        if not watch:
            logger.warning(f"Attempted to set notification for non-existent watch {watch_id}")
            return False
        
        try:
            notification_type = NotificationType(integration)
            watch.notifyon = NotificationTarget(
                channel_id=channel_id,
                integration=notification_type
            )
            return self.repo.update_watch(watch)
        except ValueError:
            logger.error(f"Invalid integration type: {integration}")
            return False
    
    def set_webhook(self, watch_id: int, webhook_url: str) -> bool:
        """Set the webhook URL for a watch."""
        watch = self.repo.get_watch(watch_id)
        if not watch:
            logger.warning(f"Attempted to set webhook for non-existent watch {watch_id}")
            return False
        
        watch.webhook = webhook_url
        return self.repo.update_watch(watch)
    
    def clear_webhook(self, watch_id: int) -> bool:
        """Clear the webhook URL for a watch."""
        watch = self.repo.get_watch(watch_id)
        if not watch:
            logger.warning(f"Attempted to clear webhook for non-existent watch {watch_id}")
            return False
        
        watch.webhook = None
        return self.repo.update_watch(watch)
    
    def get_watches_needing_check(self, check_interval: int) -> List[Watch]:
        """Get watches that need to be checked based on the interval."""
        return self.repo.get_watches_needing_check(check_interval)
    
    def mark_watch_checked(self, watch_id: int) -> bool:
        """Mark a watch as having been checked."""
        watch = self.repo.get_watch(watch_id)
        if not watch:
            return False
        
        watch.last_checked = datetime.now().timestamp()
        return self.repo.update_watch(watch)


class AdvertisementService:
    """Service for managing advertisements and price tracking."""
    
    def __init__(self, repo: RepoPort):
        self.repo = repo
    
    def process_scraped_ads(self, watch_id: int, scraped_ads: List[Dict[str, Any]]) -> Tuple[List[Advertisement], List[Advertisement]]:
        """
        Process scraped advertisements and detect new/changed ones.
        
        Returns:
            Tuple of (new_ads, price_changed_ads)
        """
        existing_ads = {ad.id: ad for ad in self.repo.get_active_advertisements(watch_id)}
        new_ads = []
        price_changed_ads = []
        
        for ad_data in scraped_ads:
            ad_id = ad_data["id"]
            
            if ad_id not in existing_ads:
                # New advertisement
                new_ad = Advertisement.create_new(ad_data, watch_id)
                self.repo.add_advertisement(ad_data, watch_id)
                new_ads.append(new_ad)
                logger.info(f"New ad found: {new_ad.title} (ID: {ad_id})")
            else:
                # Existing advertisement - check for price changes
                existing_ad = existing_ads[ad_id]
                if existing_ad.update_price(ad_data["price"]):
                    self.repo.update_advertisement(ad_data)
                    price_changed_ads.append(existing_ad)
                    logger.info(f"Price changed for ad: {existing_ad.title} (ID: {ad_id})")
        
        # Mark ads that are no longer in the scrape results as inactive
        scraped_ids = {ad["id"] for ad in scraped_ads}
        for existing_ad in existing_ads.values():
            if existing_ad.id not in scraped_ids:
                self.repo.set_advertisement_inactive(existing_ad.id)
                logger.info(f"Ad marked inactive: {existing_ad.title} (ID: {existing_ad.id})")
        
        return new_ads, price_changed_ads
    
    def get_advertisement(self, ad_id: int) -> Optional[Advertisement]:
        """Get an advertisement by ID."""
        return self.repo.get_advertisement(ad_id)
    
    def set_price_alert(self, ad_id: int, enabled: bool) -> bool:
        """Enable or disable price alerts for an advertisement."""
        return self.repo.set_advertisement_price_alert(ad_id, enabled)
    
    def get_active_ads_for_watch(self, watch_id: int) -> List[Advertisement]:
        """Get all active advertisements for a watch."""
        return self.repo.get_active_advertisements(watch_id)
    
    def force_rescrape_watch(self, watch_id: int) -> bool:
        """Force a watch to be rescaped by resetting its last_checked time."""
        watch = self.repo.get_watch(watch_id)
        if not watch:
            return False
        
        watch.last_checked = 0.0  # Force immediate check
        return self.repo.update_watch(watch)


class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, notifier: NotifierPort, webhook_notifier: Optional[NotifierPort] = None):
        self.notifier = notifier
        self.webhook_notifier = webhook_notifier
    
    async def send_new_ad_notifications(
        self, 
        watch: Watch, 
        new_ads: List[Advertisement]
    ) -> List[bool]:
        """Send notifications for new advertisements."""
        results = []
        
        for ad in new_ads:
            message = self.notifier.format_message(
                "new_ad",
                title=ad.title,
                url=ad.url,
                price=ad.price,
                city=ad.city,
                seller_name=ad.seller_name
            )
            
            # Send to integration target if configured
            if watch.notifyon:
                result = await self.notifier.send_notification(
                    watch.notifyon, 
                    message, 
                    no_preview=True
                )
                results.append(result)
            
            # Send to webhook if configured
            if watch.webhook and self.webhook_notifier:
                result = await self.webhook_notifier.send_webhook_notification(
                    watch.webhook, 
                    message
                )
                results.append(result)
        
        return results
    
    async def send_price_change_notifications(
        self, 
        watch: Watch, 
        price_changed_ads: List[Advertisement]
    ) -> List[bool]:
        """Send notifications for price changes."""
        results = []
        
        for ad in price_changed_ads:
            if not ad.price_alert:
                continue  # Skip if price alerts are disabled for this ad
            
            old_price = ad.prev_prices[-1] if ad.prev_prices else "Unknown"
            message = self.notifier.format_message(
                "price_change",
                title=ad.title,
                url=ad.url,
                old_price=old_price,
                new_price=ad.price,
                city=ad.city
            )
            
            # Send to integration target if configured
            if watch.notifyon:
                result = await self.notifier.send_notification(
                    watch.notifyon, 
                    message, 
                    no_preview=True
                )
                results.append(result)
            
            # Send to webhook if configured
            if watch.webhook and self.webhook_notifier:
                result = await self.webhook_notifier.send_webhook_notification(
                    watch.webhook, 
                    message
                )
                results.append(result)
        
        return results


class ScrapingService:
    """Service for orchestrating scraping operations."""
    
    def __init__(self, scraper: ScraperPort, repo: RepoPort):
        self.scraper = scraper
        self.repo = repo
    
    async def check_watches(self, check_interval: int) -> Dict[int, Tuple[List[Advertisement], List[Advertisement]]]:
        """
        Check all watches that need scraping.
        
        Returns:
            Dictionary mapping watch_id to (new_ads, price_changed_ads)
        """
        watches_to_check = self.repo.get_watches_needing_check(check_interval)
        results = {}
        
        for watch in watches_to_check:
            try:
                logger.info(f"Scraping watch {watch.id}: {watch.url}")
                
                # Check robots.txt once per session (handled by scraper adapter)
                # await self.scraper.check_robots_txt(base_url)
                
                # Scrape advertisements
                scraped_ads = await self.scraper.scrape_ads(watch.url)
                
                # Process the scraped ads
                ad_service = AdvertisementService(self.repo)
                new_ads, price_changed_ads = ad_service.process_scraped_ads(watch.id, scraped_ads)
                
                # Mark watch as checked
                watch_service = WatchService(self.repo)
                watch_service.mark_watch_checked(watch.id)
                
                if new_ads or price_changed_ads:
                    results[watch.id] = (new_ads, price_changed_ads)
                    logger.info(f"Watch {watch.id}: {len(new_ads)} new ads, {len(price_changed_ads)} price changes")
                else:
                    logger.info(f"Watch {watch.id}: No changes")
                
            except Exception as e:
                logger.error(f"Error scraping watch {watch.id}: {e}")
                # Continue with other watches even if one fails
        
        return results