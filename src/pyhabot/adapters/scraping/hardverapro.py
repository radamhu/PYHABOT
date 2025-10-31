"""
HardverApró scraper adapter for PYHABOT.

This adapter implements ScraperPort interface for scraping HardverApró
search result pages. It maintains compatibility with existing parsing logic
while providing async session injection.
"""

import urllib.parse
import re
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import aiohttp
from bs4 import BeautifulSoup

from ...domain.ports import ScraperPort

logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """Raised when network operations fail."""
    pass


class ParseError(Exception):
    """Raised when parsing scraped content fails."""
    pass


class HardveraproScraper(ScraperPort):
    """HardverApró implementation of scraper port."""
    
    def __init__(self, session: aiohttp.ClientSession, user_agents: List[str] = None):
        self.session = session
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        self._robots_cache = {}
    
    async def scrape_ads(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape advertisements from a given HardverApró URL.
        
        Args:
            url: The HardverApró search URL to scrape
            
        Returns:
            List of advertisement data dictionaries
            
        Raises:
            NetworkError: If scraping fails due to network issues
            ParseError: If parsing scraped content fails
        """
        try:
            ads = await self._scrape_ads_internal(url)
            logger.info(f"Successfully scraped {len(ads)} ads from {url}")
            return ads
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error while scraping {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            raise
    
    async def check_robots_txt(self, base_url: str) -> bool:
        """
        Check if scraping is allowed by robots.txt.
        
        Args:
            base_url: Base URL to check robots.txt for
            
        Returns:
            True if scraping is allowed, False otherwise
        """
        if base_url in self._robots_cache:
            return self._robots_cache[base_url]
        
        try:
            robots_url = urllib.parse.urljoin(base_url, "/robots.txt")
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    # Simple check - in production, use proper robots.txt parser
                    allowed = "Disallow: /" not in content
                    self._robots_cache[base_url] = allowed
                    return allowed
                else:
                    # If robots.txt doesn't exist or is inaccessible, assume allowed
                    self._robots_cache[base_url] = True
                    return True
        except Exception as e:
            logger.warning(f"Failed to check robots.txt for {base_url}: {e}")
            self._robots_cache[base_url] = True
            return True
    
    async def _scrape_ads_internal(self, url: str) -> List[Dict[str, Any]]:
        """Internal method for scraping with proper error handling."""
        headers = self._get_random_headers()
        
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                raise NetworkError(f"HTTP {response.status} when accessing {url}")
            
            html = BeautifulSoup(await response.text(), "html.parser")
            return self._parse_ads_from_html(html, url)
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Get random headers including user agent."""
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": random.choice(self.user_agents)
        }
    
    def _parse_ads_from_html(self, html: BeautifulSoup, source_url: str) -> List[Dict[str, Any]]:
        """Parse advertisements from HTML content."""
        ads = []
        
        try:
            parsed_url = urllib.parse.urlparse(source_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            uad_list = html.find("div", class_="uad-list")
            
            if not uad_list or not uad_list.ul or not uad_list.ul.li:
                logger.warning(f"No ad list found in HTML from {source_url}")
                return ads
            
            medias = html.findAll(class_="media")
            
            for ad in medias:
                ad_data = self._parse_single_ad(ad, base_url)
                if ad_data and self._validate_ad_data(ad_data):
                    ads.append(ad_data)
                elif ad_data:
                    logger.warning(f"Invalid ad data: {ad_data}")
            
        except Exception as e:
            logger.error(f"Error parsing HTML from {source_url}: {e}")
            raise ParseError(f"Failed to parse HTML: {e}")
        
        return ads
    
    def _parse_single_ad(self, ad_element, base_url: str) -> Optional[Dict[str, Any]]:
        """Parse a single advertisement element."""
        try:
            title = ad_element.find("div", class_="uad-col-title")
            info = ad_element.find("div", class_="uad-col-info")
            price = ad_element.find("div", class_="uad-price")
            
            if not title or not info:
                return None
            
            # Parse date
            date_value = self._parse_date(info)
            
            # Parse price
            price_value = self._parse_price(price)
            
            # Extract seller and location info
            seller_info = self._parse_seller_info(info)
            
            # Extract image
            image_url = self._parse_image_url(ad_element)
            
            return {
                "id": int(ad_element["data-uadid"]),
                "title": title.h1.a.text.strip(),
                "url": title.h1.a["href"],
                "price": price_value,
                "city": seller_info["city"],
                "date": date_value,
                "pinned": date_value == "pinned",
                "seller_name": seller_info["name"],
                "seller_url": seller_info["url"],
                "seller_rates": seller_info["rates"],
                "image": image_url
            }
            
        except (KeyError, AttributeError, ValueError, TypeError) as e:
            logger.warning(f"Error parsing ad element: {e}")
            return None
    
    def _parse_date(self, info_element) -> str:
        """Parse date from info element."""
        try:
            time_element = info_element.find("div", class_="uad-time")
            if time_element and time_element.time:
                date_text = time_element.time.text.strip()
                return convert_date(date_text) or ""
            return ""
        except Exception:
            return ""
    
    def _parse_price(self, price_element) -> Optional[int]:
        """Parse price from price element."""
        try:
            if price_element and price_element.span:
                price_text = price_element.span.text.strip()
                return convert_price(price_text)
            return None
        except Exception:
            return None
    
    def _parse_seller_info(self, info_element) -> Dict[str, str]:
        """Parse seller information from info element."""
        seller_info = {
            "city": "",
            "name": "",
            "url": "",
            "rates": ""
        }
        
        try:
            # City
            cities_element = info_element.find("div", class_="uad-cities")
            if cities_element:
                seller_info["city"] = cities_element.text.strip()
            
            # Seller info
            user_text_element = info_element.find("span", class_="uad-user-text")
            if user_text_element:
                # Seller name and URL
                if user_text_element.a:
                    seller_info["name"] = user_text_element.a.text.strip()
                    seller_info["url"] = user_text_element.a["href"]
                
                # Seller rates
                if user_text_element.span:
                    seller_info["rates"] = user_text_element.span.text.strip()
        
        except Exception as e:
            logger.warning(f"Error parsing seller info: {e}")
        
        return seller_info
    
    def _parse_image_url(self, ad_element) -> str:
        """Parse image URL from ad element."""
        try:
            if ad_element.a and ad_element.a.img:
                return ad_element.a.img["src"]
            return ""
        except Exception:
            return ""
    
    def _validate_ad_data(self, ad_data: Dict[str, Any]) -> bool:
        """Validate that ad data has all required fields."""
        required_fields = [
            'id', 'title', 'url', 'price', 'city', 
            'date', 'seller_name', 'seller_url', 'seller_rates', 'image'
        ]
        
        for field in required_fields:
            if field not in ad_data or ad_data[field] is None:
                logger.warning(f"Missing or None field '{field}' in ad data")
                return False
        
        return True


# Helper functions (ported from original scraper.py)
def convert_date(expression: str) -> Optional[str]:
    """Convert date expression to standardized format."""
    expression = expression.strip()
    
    if re.match(r"\d{4}-\d{2}-\d{2}", expression):
        try:
            ret_date = datetime.strptime(expression, "%Y-%m-%d")
            return ret_date.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return None
    elif re.match(r"ma \d{2}:\d{2}", expression):
        try:
            now = datetime.now()
            time_part = expression.split()[1]
            ret_date = datetime.strptime(time_part, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            return ret_date.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return None
    elif re.match(r"tegnap \d{2}:\d{2}", expression):
        try:
            now = datetime.now()
            time_part = expression.split()[1]
            ret_date = datetime.strptime(time_part, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            ) - timedelta(days=1)
            return ret_date.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return None
    elif expression.lower() == "előresorolva":
        return "pinned"
    else:
        return None


def convert_price(price: str) -> Optional[int]:
    """Convert price string to integer value."""
    price = price.strip()
    
    if price.lower() == "keresem":
        return None
    
    # Handle millions (e.g., "1.5M Ft")
    if "M" in price:
        match = re.search(r"([0-9,]+)M Ft", price)
        if match:
            return int(float(match.group(1).replace(",", ".")) * 1_000_000)
    
    # Handle regular prices (e.g., "100 000 Ft")
    match = re.search(r"([0-9 ]+) Ft", price)
    if match:
        return int(match.group(1).replace(" ", ""))
    
    return None


def get_url_params(url: str) -> tuple[str, str, str]:
    """Extract URL parameters for search context."""
    parsed_url = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed_url.query)
    stext = params["stext"][0] if "stext" in params else "-"
    minprice = params["minprice"][0] if "minprice" in params else "0"
    maxprice = params["maxprice"][0] if "maxprice" in params else "∞"
    return stext, minprice, maxprice