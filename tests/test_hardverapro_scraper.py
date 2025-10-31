"""
Unit tests for HardverApró scraper adapter.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bs4 import BeautifulSoup
import aiohttp

from src.pyhabot.adapters.scraping.hardverapro import (
    HardveraproScraper, 
    NetworkError, 
    ParseError
)


@pytest.fixture
def mock_session():
    """Mock aiohttp session for testing."""
    return AsyncMock()


def create_mock_context(mock_response):
    """Create a proper async context manager mock."""
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    return mock_context


class TestHardveraproScraper:
    """Test cases for HardveraproScraper class."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp ClientSession."""
        return AsyncMock()
    
    @pytest.fixture
    def scraper(self, mock_session):
        """Create scraper instance with mock session."""
        return HardveraproScraper(mock_session)
    
    @pytest.fixture
    def sample_html(self):
        """Load sample HTML from fixture."""
        with open("tests/fixtures/hardverapro_list.html", "r", encoding="utf-8") as f:
            return f.read()
    
    @pytest.fixture
    def empty_html(self):
        """Load empty HTML from fixture."""
        with open("tests/fixtures/hardverapro_empty.html", "r", encoding="utf-8") as f:
            return f.read()
    
    @pytest.fixture
    def malformed_html(self):
        """Load malformed HTML from fixture."""
        with open("tests/fixtures/hardverapro_malformed.html", "r", encoding="utf-8") as f:
            return f.read()

    def test_init_default_user_agents(self, mock_session):
        """Test scraper initialization with default user agents."""
        scraper = HardveraproScraper(mock_session)
        assert len(scraper.user_agents) == 3
        assert all("Mozilla" in agent for agent in scraper.user_agents)
    
    def test_init_custom_user_agents(self, mock_session):
        """Test scraper initialization with custom user agents."""
        custom_agents = ["CustomAgent/1.0", "AnotherAgent/2.0"]
        scraper = HardveraproScraper(mock_session, custom_agents)
        assert scraper.user_agents == custom_agents
    
    def test_get_random_headers(self, scraper):
        """Test generating random headers."""
        headers = scraper._get_random_headers()
        
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers
        assert "Connection" in headers
        assert "Upgrade-Insecure-Requests" in headers
        assert "User-Agent" in headers
        assert headers["User-Agent"] in scraper.user_agents
    
    @pytest.mark.asyncio
    async def test_scrape_ads_success(self, scraper, sample_html):
        """Test successful ad scraping."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_html)
        
        scraper.session.get.return_value = create_mock_context(mock_response)
        
        url = "https://hardverapro.hu/search"
        ads = await scraper.scrape_ads(url)
        
        assert len(ads) == 4  # Only valid ads should be parsed
        
        # Check first ad
        first_ad = ads[0]
        assert first_ad["id"] == 123456
        assert first_ad["title"] == "Test termék 1 - Eladó"
        assert first_ad["url"] == "https://hardverapro.hu/termek/test-termek-1/123456.html"
        assert first_ad["price"] == 100000
        assert first_ad["city"] == "Budapest"
        assert first_ad["seller_name"] == "testuser1"
        assert first_ad["seller_rates"] == "4.5"
        assert first_ad["image"] == "https://hardverapro.hu/media/test1.jpg"
        assert not first_ad["pinned"]
    
    @pytest.mark.asyncio
    async def test_scrape_ads_empty_list(self, scraper, empty_html):
        """Test scraping empty ad list."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=empty_html)
        
        scraper.session.get.return_value.__aenter__.return_value = mock_response
        
        url = "https://hardverapro.hu/search"
        ads = await scraper.scrape_ads(url)
        
        assert len(ads) == 0
    
    @pytest.mark.asyncio
    async def test_scrape_ads_malformed_content(self, scraper, malformed_html):
        """Test scraping malformed HTML content."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=malformed_html)
        
        scraper.session.get.return_value.__aenter__.return_value = mock_response
        
        url = "https://hardverapro.hu/search"
        ads = await scraper.scrape_ads(url)
        
        # Should return empty list as no valid ads found
        assert len(ads) == 0
    
    @pytest.mark.asyncio
    async def test_scrape_ads_network_error(self, scraper):
        """Test handling network errors."""
        scraper.session.get.side_effect = aiohttp.ClientError("Connection failed")
        
        url = "https://hardverapro.hu/search"
        
        with pytest.raises(NetworkError, match="Network error while scraping"):
            await scraper.scrape_ads(url)
    
    @pytest.mark.asyncio
    async def test_scrape_ads_http_error(self, scraper):
        """Test handling HTTP errors."""
        mock_response = AsyncMock()
        mock_response.status = 404
        
        scraper.session.get.return_value.__aenter__.return_value = mock_response
        
        url = "https://hardverapro.hu/search"
        
        with pytest.raises(NetworkError, match="HTTP 404"):
            await scraper.scrape_ads(url)
    
    @pytest.mark.asyncio
    async def test_check_robots_txt_success(self, scraper):
        """Test successful robots.txt check."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="User-agent: *\nAllow: /")
        
        scraper.session.get.return_value.__aenter__.return_value = mock_response
        
        result = await scraper.check_robots_txt("https://hardverapro.hu")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_robots_txt_disallowed(self, scraper):
        """Test robots.txt with disallow."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="User-agent: *\nDisallow: /")
        
        scraper.session.get.return_value.__aenter__.return_value = mock_response
        
        result = await scraper.check_robots_txt("https://hardverapro.hu")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_robots_txt_missing(self, scraper):
        """Test missing robots.txt."""
        mock_response = AsyncMock()
        mock_response.status = 404
        
        scraper.session.get.return_value.__aenter__.return_value = mock_response
        
        result = await scraper.check_robots_txt("https://hardverapro.hu")
        assert result is True  # Assume allowed if robots.txt doesn't exist
    
    @pytest.mark.asyncio
    async def test_check_robots_txt_network_error(self, scraper):
        """Test network error when checking robots.txt."""
        scraper.session.get.side_effect = aiohttp.ClientError("Connection failed")
        
        result = await scraper.check_robots_txt("https://hardverapro.hu")
        assert result is True  # Assume allowed on network error
    
    def test_parse_ads_from_html_valid(self, scraper, sample_html):
        """Test parsing valid HTML."""
        html = BeautifulSoup(sample_html, "html.parser")
        url = "https://hardverapro.hu/search"
        
        ads = scraper._parse_ads_from_html(html, url)
        
        assert len(ads) == 4  # Only valid ads
        
        # Test pinned ad
        pinned_ad = next(ad for ad in ads if ad["id"] == 901234)
        assert pinned_ad["pinned"] is True
        assert pinned_ad["price"] is None  # "keresem" should return None
    
    def test_parse_ads_from_html_no_list(self, scraper):
        """Test parsing HTML without ad list."""
        html = BeautifulSoup("<html><body>No ads here</body></html>", "html.parser")
        url = "https://hardverapro.hu/search"
        
        ads = scraper._parse_ads_from_html(html, url)
        assert len(ads) == 0
    
    def test_validate_ad_data_valid(self, scraper):
        """Test validating valid ad data."""
        ad_data = {
            "id": 123,
            "title": "Test Ad",
            "url": "https://example.com/ad/123",
            "price": 1000,
            "city": "Budapest",
            "date": "2025-10-30 10:00",
            "seller_name": "testuser",
            "seller_url": "https://example.com/user/testuser",
            "seller_rates": "4.5",
            "image": "https://example.com/image/123.jpg"
        }
        
        assert scraper._validate_ad_data(ad_data) is True
    
    def test_validate_ad_data_missing_field(self, scraper):
        """Test validating ad data with missing field."""
        ad_data = {
            "id": 123,
            "title": "Test Ad",
            # Missing url field
            "price": 1000,
            "city": "Budapest",
            "date": "2025-10-30 10:00",
            "seller_name": "testuser",
            "seller_url": "https://example.com/user/testuser",
            "seller_rates": "4.5",
            "image": "https://example.com/image/123.jpg"
        }
        
        assert scraper._validate_ad_data(ad_data) is False
    
    def test_validate_ad_data_none_field(self, scraper):
        """Test validating ad data with None field."""
        ad_data = {
            "id": 123,
            "title": "Test Ad",
            "url": None,  # None value
            "price": 1000,
            "city": "Budapest",
            "date": "2025-10-30 10:00",
            "seller_name": "testuser",
            "seller_url": "https://example.com/user/testuser",
            "seller_rates": "4.5",
            "image": "https://example.com/image/123.jpg"
        }
        
        assert scraper._validate_ad_data(ad_data) is False