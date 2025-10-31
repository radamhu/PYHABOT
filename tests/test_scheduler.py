"""
Tests for the scheduler module.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.pyhabot.scheduler import SchedulerRunner, SchedulerConfig
from src.pyhabot.domain.models import Watch, Advertisement, NotificationTarget, NotificationType


@pytest.fixture
def mock_scraper():
    """Mock scraper port."""
    scraper = AsyncMock()
    scraper.scrape_ads.return_value = [
        {
            "id": "123",
            "title": "Test Ad",
            "url": "https://example.com/ad/123",
            "price": 10000,
            "city": "Budapest",
            "seller_name": "Test Seller",
            "date": "2025-10-30",
            "pinned": False,
            "seller_url": "https://example.com/seller/123",
            "seller_rates": "5.0",
            "image": "https://example.com/image/123.jpg"
        }
    ]
    return scraper


@pytest.fixture
def mock_repo():
    """Mock repository port."""
    repo = MagicMock()
    repo.get_watches_needing_check.return_value = [
        Watch(
            id=1,
            url="https://example.com/search",
            last_checked=0.0,
            notifyon=NotificationTarget(
                channel_id="test_channel",
                integration=NotificationType.DISCORD
            ),
            webhook=None
        )
    ]
    repo.get_active_advertisements.return_value = []
    return repo


@pytest.fixture
def mock_notifier():
    """Mock notifier port."""
    notifier = AsyncMock()
    notifier.send_notification.return_value = True
    notifier.send_webhook_notification.return_value = True
    notifier.format_message.return_value = "Test message"
    return notifier


@pytest.fixture
def scheduler_config():
    """Scheduler configuration for testing."""
    return SchedulerConfig(
        check_interval=1,  # 1 second for fast testing
        jitter_min=0.8,
        jitter_max=1.2,
        max_retries=2,
        base_backoff=0.1,
        max_backoff=1.0,
        request_delay_min=0.01,
        request_delay_max=0.05
    )


@pytest.fixture
def scheduler(mock_scraper, mock_repo, mock_notifier, scheduler_config):
    """Scheduler instance for testing."""
    return SchedulerRunner(
        scraper=mock_scraper,
        repo=mock_repo,
        notifier=mock_notifier,
        config=scheduler_config
    )


@pytest.mark.asyncio
async def test_scheduler_start_stop(scheduler):
    """Test starting and stopping the scheduler."""
    assert not scheduler.is_running
    
    # Start scheduler
    await scheduler.start()
    assert scheduler.is_running
    
    # Stop scheduler
    await scheduler.stop()
    assert not scheduler.is_running


@pytest.mark.asyncio
async def test_scheduler_processes_watches(scheduler, mock_scraper, mock_repo, mock_notifier):
    """Test that scheduler processes watches correctly."""
    # Start scheduler
    await scheduler.start()
    
    # Wait a bit for processing
    await asyncio.sleep(0.2)
    
    # Stop scheduler
    await scheduler.stop()
    
    # Verify scraper was called
    mock_scraper.scrape_ads.assert_called_once_with("https://example.com/search")
    
    # Verify notifications were sent
    mock_notifier.send_notification.assert_called()
    mock_notifier.format_message.assert_called()


@pytest.mark.asyncio
async def test_scheduler_handles_errors(scheduler, mock_scraper, mock_repo):
    """Test that scheduler handles scraping errors gracefully."""
    # Make scraper raise an exception
    mock_scraper.scrape_ads.side_effect = Exception("Network error")
    
    # Start scheduler
    await scheduler.start()
    
    # Wait a bit for processing
    await asyncio.sleep(0.2)
    
    # Stop scheduler
    await scheduler.stop()
    
    # Verify scraper was called despite error
    mock_scraper.scrape_ads.assert_called()


@pytest.mark.asyncio
async def test_scheduler_jitter_delay(scheduler):
    """Test that scheduler applies jitter delays."""
    with patch('asyncio.sleep') as mock_sleep, \
         patch('random.uniform') as mock_random:
        mock_sleep.return_value = None
        mock_random.return_value = 1.5  # Force positive jitter
        
        # Process a watch
        watch = scheduler.watch_service.get_watches_needing_check(1)[0]
        await scheduler._process_watch(watch)
        
        # Verify sleep was called (jitter delay)
        mock_sleep.assert_called()
        mock_random.assert_called()


def test_scheduler_config_defaults():
    """Test scheduler configuration defaults."""
    config = SchedulerConfig()
    
    assert config.check_interval == 300
    assert config.jitter_min == 0.8
    assert config.jitter_max == 1.2
    assert config.max_retries == 3
    assert config.base_backoff == 1.0
    assert config.max_backoff == 60.0
    assert config.request_delay_min == 1.0
    assert config.request_delay_max == 3.0


def test_scheduler_config_custom():
    """Test scheduler configuration with custom values."""
    config = SchedulerConfig(
        check_interval=600,
        jitter_min=0.5,
        jitter_max=1.5,
        max_retries=5,
        base_backoff=2.0,
        max_backoff=120.0,
        request_delay_min=2.0,
        request_delay_max=5.0
    )
    
    assert config.check_interval == 600
    assert config.jitter_min == 0.5
    assert config.jitter_max == 1.5
    assert config.max_retries == 5
    assert config.base_backoff == 2.0
    assert config.max_backoff == 120.0
    assert config.request_delay_min == 2.0
    assert config.request_delay_max == 5.0