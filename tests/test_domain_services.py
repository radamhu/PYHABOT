"""
Unit tests for domain services.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.pyhabot.domain.services import (
    AdvertisementService,
    WatchService,
    NotificationService
)
from src.pyhabot.domain.models import Watch, Advertisement, NotificationTarget, NotificationType
from src.pyhabot.domain.ports import RepoPort, ScraperPort, NotifierPort


class TestAdvertisementService:
    """Test cases for AdvertisementService."""
    
    @pytest.fixture
    def mock_repo(self):
        """Mock repository."""
        return MagicMock(spec=RepoPort)
    
    @pytest.fixture
    def ad_service(self, mock_repo):
        """Create advertisement service."""
        return AdvertisementService(mock_repo)
    
    @pytest.fixture
    def sample_watch_id(self):
        """Sample watch ID for testing."""
        return 1
    
    @pytest.fixture
    def sample_ads(self):
        """Sample advertisements for testing."""
        return [
            {
                "id": 123,
                "title": "Test Ad 1",
                "url": "https://hardverapro.hu/ad/123",
                "price": 100000,
                "city": "Budapest",
                "date": "2025-10-30 10:00",
                "pinned": False,
                "seller_name": "seller1",
                "seller_url": "https://hardverapro.hu/user/seller1",
                "seller_rates": "4.5",
                "image": "https://hardverapro.hu/img/123.jpg"
            },
            {
                "id": 456,
                "title": "Test Ad 2",
                "url": "https://hardverapro.hu/ad/456",
                "price": 200000,
                "city": "Debrecen",
                "date": "2025-10-30 11:00",
                "pinned": False,
                "seller_name": "seller2",
                "seller_url": "https://hardverapro.hu/user/seller2",
                "seller_rates": "4.0",
                "image": "https://hardverapro.hu/img/456.jpg"
            }
        ]
    
    def test_process_scraped_ads_new_ads(self, ad_service, sample_watch_id, sample_ads):
        """Test processing scrape results with new advertisements."""
        # Mock repository to return no existing ads
        ad_service.repo.get_active_advertisements.return_value = []
        
        # Process scrape results
        new_ads, price_changes = ad_service.process_scraped_ads(sample_watch_id, sample_ads)
        
        # Should have 2 new ads, no price changes
        assert len(new_ads) == 2
        assert len(price_changes) == 0
        
        # Verify ads were saved
        assert ad_service.repo.add_advertisement.call_count == 2
    
    def test_process_scraped_ads_existing_ads_no_changes(self, ad_service, sample_watch_id, sample_ads):
        """Test processing scrape results with existing ads and no changes."""
        # Mock repository to return existing ads with same prices
        existing_ad = Advertisement(
            id=123,
            title="Test Ad 1",
            url="https://hardverapro.hu/ad/123",
            price=100000,
            prev_prices=[],
            city="Budapest",
            date="2025-10-30 10:00",
            pinned=False,
            seller_name="seller1",
            seller_url="https://hardverapro.hu/user/seller1",
            seller_rates="4.5",
            image="https://hardverapro.hu/img/123.jpg",
            watch_id=sample_watch_id,
            active=True
        )
        ad_service.repo.get_active_advertisements.return_value = [existing_ad]
        
        # Process scrape results
        new_ads, price_changes = ad_service.process_scraped_ads(sample_watch_id, sample_ads)
        
        # Should have no new ads, no price changes
        assert len(new_ads) == 0
        assert len(price_changes) == 0
        
        # Verify no new insertions
        ad_service.repo.add_advertisement.assert_not_called()
        ad_service.repo.update_advertisement.assert_not_called()
    
    def test_process_scraped_ads_price_change(self, ad_service, sample_watch_id, sample_ads):
        """Test processing scrape results with price changes."""
        # Mock repository to return existing ad with different price
        existing_ad = Advertisement(
            id=123,
            title="Test Ad 1",
            url="https://hardverapro.hu/ad/123",
            price=90000,  # Different price
            prev_prices=[80000],
            city="Budapest",
            date="2025-10-30 10:00",
            pinned=False,
            seller_name="seller1",
            seller_url="https://hardverapro.hu/user/seller1",
            seller_rates="4.5",
            image="https://hardverapro.hu/img/123.jpg",
            watch_id=sample_watch_id,
            active=True
        )
        ad_service.repo.get_active_advertisements.return_value = [existing_ad]
        
        # Process scrape results
        new_ads, price_changes = ad_service.process_scraped_ads(sample_watch_id, sample_ads)
        
        # Should have no new ads, 1 price change
        assert len(new_ads) == 0
        assert len(price_changes) == 1
        
        # Verify price change details
        price_change_ad = price_changes[0]
        assert price_change_ad.id == 123
        assert price_change_ad.price == 100000  # Updated price
        
        # Verify advertisement was updated
        ad_service.repo.update_advertisement.assert_called_once()
    
    def test_process_scraped_ads_inactive_ads(self, ad_service, sample_watch_id, sample_ads):
        """Test processing scrape results with inactive ads."""
        # Mock repository to return existing ads that are no longer in scrape results
        existing_ads = [
            Advertisement(
                id=789,
                title="Old Ad 1",
                url="https://hardverapro.hu/ad/789",
                price=50000,
                prev_prices=[],
                city="Budapest",
                date="2025-10-29 10:00",
                pinned=False,
                seller_name="seller3",
                seller_url="https://hardverapro.hu/user/seller3",
                seller_rates="3.5",
                image="https://hardverapro.hu/img/789.jpg",
                watch_id=sample_watch_id,
                active=True
            )
        ]
        ad_service.repo.get_active_advertisements.return_value = existing_ads
        
        # Process scrape results
        new_ads, price_changes = ad_service.process_scraped_ads(sample_watch_id, sample_ads)
        
        # Should have 2 new ads, no price changes
        assert len(new_ads) == 2
        assert len(price_changes) == 0
        
        # Verify old ads were marked inactive
        ad_service.repo.set_advertisement_inactive.assert_called_once_with(789)


class TestWatchService:
    """Test cases for WatchService."""
    
    @pytest.fixture
    def mock_repo(self):
        """Mock repository."""
        return MagicMock(spec=RepoPort)
    
    @pytest.fixture
    def watch_service(self, mock_repo):
        """Create watch service."""
        return WatchService(mock_repo)
    
    @pytest.fixture
    def sample_watch(self):
        """Sample watch for testing."""
        return Watch(
            id=1,
            url="https://hardverapro.hu/search/test",
            last_checked=0.0,
            notifyon=NotificationTarget(
                channel_id="test_channel",
                integration=NotificationType.DISCORD
            ),
            webhook=None
        )
    
    def test_create_watch(self, watch_service):
        """Test creating a new watch."""
        # Mock repository to return success
        watch_service.repo.add_watch.return_value = 1
        
        result = watch_service.create_watch("https://hardverapro.hu/search/test")
        
        assert result == 1
        watch_service.repo.add_watch.assert_called_once_with("https://hardverapro.hu/search/test")
    
    def test_get_watches_needing_check(self, watch_service):
        """Test getting watches that need checking."""
        watches = [
            Watch(
                id=1,
                url="https://hardverapro.hu/search/test1",
                last_checked=0.0,  # Never checked
                notifyon=NotificationTarget(
                    channel_id="channel1",
                    integration=NotificationType.DISCORD
                ),
                webhook=None
            )
        ]
        watch_service.repo.get_watches_needing_check.return_value = watches
        
        result = watch_service.get_watches_needing_check(1800)  # 30 minutes
        
        assert len(result) == 1
        assert result[0].id == 1
        watch_service.repo.get_watches_needing_check.assert_called_once_with(1800)
    
    def test_mark_watch_checked(self, watch_service, sample_watch):
        """Test marking watch as checked."""
        # Mock repository to return the watch
        watch_service.repo.get_watch.return_value = sample_watch
        watch_service.repo.update_watch.return_value = True
        
        result = watch_service.mark_watch_checked(sample_watch.id)
        
        assert result is True
        watch_service.repo.update_watch.assert_called_once()
    
    def test_remove_watch(self, watch_service, sample_watch):
        """Test removing a watch."""
        # Mock repository to return the watch and successful removal
        watch_service.repo.get_watch.return_value = sample_watch
        watch_service.repo.remove_watch.return_value = True
        
        result = watch_service.remove_watch(sample_watch.id)
        
        assert result is True
        watch_service.repo.remove_watch.assert_called_once_with(sample_watch.id)
    
    def test_list_watches(self, watch_service, sample_watch):
        """Test listing all watches."""
        watches = [sample_watch]
        watch_service.repo.get_all_watches.return_value = watches
        
        result = watch_service.get_all_watches()
        
        assert len(result) == 1
        assert result[0].id == sample_watch.id
        watch_service.repo.get_all_watches.assert_called_once()


class TestNotificationService:
    """Test cases for NotificationService."""
    
    @pytest.fixture
    def mock_notifier(self):
        """Mock notifier."""
        return AsyncMock(spec=NotifierPort)
    
    @pytest.fixture
    def notification_service(self, mock_notifier):
        """Create notification service."""
        return NotificationService(mock_notifier)
    
    @pytest.fixture
    def sample_notification_target(self):
        """Sample notification target."""
        return NotificationTarget(
            channel_id="test_channel",
            integration=NotificationType.DISCORD
        )
    
    @pytest.fixture
    def sample_watch(self):
        """Sample watch for testing."""
        return Watch(
            id=1,
            url="https://hardverapro.hu/search/test",
            last_checked=0.0,
            notifyon=NotificationTarget(
                channel_id="test_channel",
                integration=NotificationType.DISCORD
            ),
            webhook=None
        )
    
    @pytest.mark.asyncio
    async def test_send_new_ad_notifications(self, notification_service, mock_notifier, sample_watch):
        """Test sending new ads notification."""
        new_ads = [
            Advertisement(
                id=123,
                title="Test Ad",
                url="https://hardverapro.hu/ad/123",
                price=100000,
                prev_prices=[],
                city="Budapest",
                date="2025-10-30 10:00",
                pinned=False,
                seller_name="seller1",
                seller_url="https://hardverapro.hu/user/seller1",
                seller_rates="4.5",
                image="https://hardverapro.hu/img/123.jpg",
                watch_id=sample_watch.id,
                active=True
            )
        ]
        
        # Mock the notifier methods
        mock_notifier.format_message.return_value = "Test message"
        mock_notifier.send_notification.return_value = True
        
        results = await notification_service.send_new_ad_notifications(sample_watch, new_ads)
        
        assert len(results) == 1
        mock_notifier.format_message.assert_called_once()
        mock_notifier.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_price_change_notifications(self, notification_service, mock_notifier, sample_watch):
        """Test sending price change notification."""
        price_changed_ads = [
            Advertisement(
                id=123,
                title="Test Ad",
                url="https://hardverapro.hu/ad/123",
                price=100000,
                prev_prices=[90000],
                city="Budapest",
                date="2025-10-30 10:00",
                pinned=False,
                seller_name="seller1",
                seller_url="https://hardverapro.hu/user/seller1",
                seller_rates="4.5",
                image="https://hardverapro.hu/img/123.jpg",
                watch_id=sample_watch.id,
                active=True,
                price_alert=True
            )
        ]
        
        # Mock the notifier methods
        mock_notifier.format_message.return_value = "Price change message"
        mock_notifier.send_notification.return_value = True
        
        results = await notification_service.send_price_change_notifications(sample_watch, price_changed_ads)
        
        assert len(results) == 1
        mock_notifier.format_message.assert_called_once()
        mock_notifier.send_notification.assert_called_once()