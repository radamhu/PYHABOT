"""
End-to-end integration test for terminal integration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from io import StringIO
import tempfile
import os
from pathlib import Path

from src.pyhabot.adapters.repos.tinydb_repo import TinyDBRepository
from src.pyhabot.adapters.scraping.hardverapro import HardveraproScraper
from src.pyhabot.domain.services import ScrapingService
from src.pyhabot.config import Config


class TestTerminalIntegrationE2E:
    """End-to-end test for terminal integration with mocked network."""
    
    @pytest.fixture
    def temp_db_file(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"_default": {}}')
            temp_path = f.name
        
        # Return the directory containing the file
        yield Path(temp_path).parent
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def sample_html(self):
        """Load sample HTML from fixture."""
        with open("tests/fixtures/hardverapro_list.html", "r", encoding="utf-8") as f:
            return f.read()
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp ClientSession."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_scraping_with_mock_network(self, temp_db_file, sample_html, mock_session):
        """Test scraping flow with mocked network responses."""
        
        # Setup repository with temporary database
        repo = TinyDBRepository(temp_db_file)
        
        # Create a watch
        watch_id = repo.add_watch("https://hardverapro.hu/search/test")
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_html)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Create scraper with mocked session
        scraper = HardveraproScraper(mock_session)
        
        # Create scraping service
        scraping_service = ScrapingService(scraper, repo)
        
        # Execute scraping
        results = await scraping_service.check_watches(1)  # Check all watches
        
        # Verify scraping results
        assert watch_id in results
        new_ads, price_changed_ads = results[watch_id]
        assert len(new_ads) == 4  # Should find 4 valid ads from fixture
        assert len(price_changed_ads) == 0
        
        # Verify ads were saved to database
        saved_ads = repo.get_active_advertisements(watch_id)
        assert len(saved_ads) == 4
        
        # Verify specific ad data
        ad_ids = [ad.id for ad in saved_ads]
        assert 123456 in ad_ids
        assert 789012 in ad_ids
        assert 345678 in ad_ids
        assert 901234 in ad_ids
        
        # Verify watch was marked as checked
        watch = repo.get_watch(watch_id)
        assert watch is not None
        assert watch.last_checked > 0
    
    @pytest.mark.asyncio
    async def test_price_change_detection(self, temp_db_file, sample_html, mock_session):
        """Test price change detection with existing ads."""
        
        # Setup repository with temporary database
        repo = TinyDBRepository(temp_db_file)
        
        # Create a watch
        watch_id = repo.add_watch("https://hardverapro.hu/search/test")
        
        # Add existing advertisement with different price
        existing_ad_data = {
            "id": 123456,
            "title": "Test termék 1 - Eladó",
            "url": "https://hardverapro.hu/termek/test-termek-1/123456.html",
            "price": 90000,  # Different from fixture
            "city": "Budapest",
            "date": "2025-10-30 10:00",
            "pinned": False,
            "seller_name": "testuser1",
            "seller_url": "https://hardverapro.hu/profil/testuser1/",
            "seller_rates": "4.5",
            "image": "https://hardverapro.hu/media/test1.jpg",
            "watch_id": watch_id,
            "active": True,
            "prev_prices": [80000],
            "price_alert": True
        }
        repo.add_advertisement(existing_ad_data, watch_id)
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_html)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Create scraper with mocked session
        scraper = HardveraproScraper(mock_session)
        
        # Create scraping service
        scraping_service = ScrapingService(scraper, repo)
        
        # Execute scraping
        results = await scraping_service.check_watches(1)  # Check all watches
        
        # Verify scraping results
        assert watch_id in results
        new_ads, price_changed_ads = results[watch_id]
        assert len(new_ads) == 3  # 3 new ads (one is existing)
        assert len(price_changed_ads) == 1  # 1 price change
        
        # Verify price change details
        price_changed_ad = price_changed_ads[0]
        assert price_changed_ad.id == 123456
        assert price_changed_ad.price == 100000  # Updated price from fixture
        assert 90000 in price_changed_ad.prev_prices  # Previous price tracked
    
    @pytest.mark.asyncio
    async def test_no_changes_scenario(self, temp_db_file, sample_html, mock_session):
        """Test scenario with no new ads or price changes."""
        
        # Setup repository with temporary database
        repo = TinyDBRepository(temp_db_file)
        
        # Create a watch
        watch_id = repo.add_watch("https://hardverapro.hu/search/test")
        
        # Add all existing advertisements from fixture
        existing_ads_data = [
            {
                "id": 123456,
                "title": "Test termék 1 - Eladó",
                "url": "https://hardverapro.hu/termek/test-termek-1/123456.html",
                "price": 100000,
                "city": "Budapest",
                "date": "2025-10-30 10:00",
                "pinned": False,
                "seller_name": "testuser1",
                "seller_url": "https://hardverapro.hu/profil/testuser1/",
                "seller_rates": "4.5",
                "image": "https://hardverapro.hu/media/test1.jpg",
                "watch_id": watch_id,
                "active": True,
                "prev_prices": [],
                "price_alert": False
            },
            {
                "id": 789012,
                "title": "Test termék 2 - Nagyon jó állapotú",
                "url": "https://hardverapro.hu/termek/test-termek-2/789012.html",
                "price": 250000,
                "city": "Debrecen",
                "date": "2025-10-30 11:00",
                "pinned": False,
                "seller_name": "testuser2",
                "seller_url": "https://hardverapro.hu/profil/testuser2/",
                "seller_rates": "5.0",
                "image": "https://hardverapro.hu/media/test2.jpg",
                "watch_id": watch_id,
                "active": True,
                "prev_prices": [],
                "price_alert": False
            },
            {
                "id": 345678,
                "title": "Test termék 3 - Csere is érdekel",
                "url": "https://hardverapro.hu/termek/test-termek-3/345678.html",
                "price": 1500000,
                "city": "Szeged",
                "date": "2025-10-28",
                "pinned": False,
                "seller_name": "testuser3",
                "seller_url": "https://hardverapro.hu/profil/testuser3/",
                "seller_rates": "3.8",
                "image": "https://hardverapro.hu/media/test3.jpg",
                "watch_id": watch_id,
                "active": True,
                "prev_prices": [],
                "price_alert": False
            },
            {
                "id": 901234,
                "title": "Test termék 4 - Előresorolva",
                "url": "https://hardverapro.hu/termek/test-termek-4/901234.html",
                "price": None,  # "keresem"
                "city": "Pécs",
                "date": "pinned",
                "pinned": True,
                "seller_name": "testuser4",
                "seller_url": "https://hardverapro.hu/profil/testuser4/",
                "seller_rates": "4.2",
                "image": "https://hardverapro.hu/media/test4.jpg",
                "watch_id": watch_id,
                "active": True,
                "prev_prices": [],
                "price_alert": False
            }
        ]
        
        for ad_data in existing_ads_data:
            repo.add_advertisement(ad_data, watch_id)
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_html)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Create scraper with mocked session
        scraper = HardveraproScraper(mock_session)
        
        # Create scraping service
        scraping_service = ScrapingService(scraper, repo)
        
        # Execute scraping
        results = await scraping_service.check_watches(1)  # Check all watches
        
        # Verify scraping results - no changes
        assert watch_id in results
        new_ads, price_changed_ads = results[watch_id]
        assert len(new_ads) == 0  # No new ads
        assert len(price_changed_ads) == 0  # No price changes
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, temp_db_file, mock_session):
        """Test handling of network errors during scraping."""
        
        # Setup repository with temporary database
        repo = TinyDBRepository(temp_db_file)
        
        # Create a watch
        watch_id = repo.add_watch("https://hardverapro.hu/search/test")
        
        # Mock network error
        import aiohttp
        mock_session.get.side_effect = aiohttp.ClientError("Connection failed")
        
        # Create scraper with mocked session
        scraper = HardveraproScraper(mock_session)
        
        # Create scraping service
        scraping_service = ScrapingService(scraper, repo)
        
        # Execute scraping - should handle error gracefully
        results = await scraping_service.check_watches(1)  # Check all watches
        
        # Should return empty results due to network error
        assert len(results) == 0
        
        # Watch should still be marked as checked (error handling)
        watch = repo.get_watch(watch_id)
        assert watch is not None
        assert watch.last_checked > 0  # Should be updated
    
    @pytest.mark.asyncio
    async def test_empty_html_response(self, temp_db_file, mock_session):
        """Test handling of empty HTML response."""
        
        # Setup repository with temporary database
        repo = TinyDBRepository(temp_db_file)
        
        # Create a watch
        watch_id = repo.add_watch("https://hardverapro.hu/search/test")
        
        # Load empty HTML fixture
        with open("tests/fixtures/hardverapro_empty.html", "r", encoding="utf-8") as f:
            empty_html = f.read()
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=empty_html)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Create scraper with mocked session
        scraper = HardveraproScraper(mock_session)
        
        # Create scraping service
        scraping_service = ScrapingService(scraper, repo)
        
        # Execute scraping
        results = await scraping_service.check_watches(1)  # Check all watches
        
        # Verify scraping results - no ads found
        assert watch_id in results
        new_ads, price_changed_ads = results[watch_id]
        assert len(new_ads) == 0  # No new ads
        assert len(price_changed_ads) == 0  # No price changes
        
        # Verify no ads were saved to database
        saved_ads = repo.get_active_advertisements(watch_id)
        assert len(saved_ads) == 0