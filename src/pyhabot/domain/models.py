"""
Domain models for PYHABOT.

These models represent the core business entities and contain no infrastructure concerns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class NotificationType(Enum):
    """Types of notification targets."""
    WEBHOOK = "webhook"


@dataclass
class NotificationTarget:
    """Target for sending notifications."""
    channel_id: str
    integration: NotificationType
    webhook_url: Optional[str] = None


@dataclass
class Watch:
    """Represents a watch configuration for monitoring a search URL."""
    id: int
    url: str
    last_checked: float
    notifyon: Optional[NotificationTarget] = None
    webhook: Optional[str] = None
    
    @classmethod
    def create_new(cls, id: int, url: str) -> "Watch":
        """Create a new watch with default values."""
        return cls(
            id=id,
            url=url,
            last_checked=0.0,  # Never checked
            notifyon=None,
            webhook=None
        )
    
    def needs_check(self, check_interval: int) -> bool:
        """Determine if this watch needs to be checked based on interval."""
        now = datetime.now().timestamp()
        return (now - self.last_checked) >= check_interval
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        result = {
            "id": self.id,
            "url": self.url,
            "last_checked": self.last_checked,
            "webhook": self.webhook
        }
        if self.notifyon:
            result["notifyon"] = {
                "channel_id": self.notifyon.channel_id,
                "integration": self.notifyon.integration.value
            }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Watch":
        """Create from dictionary from persistence."""
        notifyon = None
        if "notifyon" in data and data["notifyon"]:
            notifyon_data = data["notifyon"]
            notifyon = NotificationTarget(
                channel_id=notifyon_data["channel_id"],
                integration=NotificationType(notifyon_data["integration"])
            )
        
        return cls(
            id=data["id"],
            url=data["url"],
            last_checked=data["last_checked"],
            notifyon=notifyon,
            webhook=data.get("webhook")
        )


@dataclass
class Advertisement:
    """Represents an advertisement from HardverApró."""
    id: int
    title: str
    url: str
    price: Optional[int]
    city: str
    date: str
    pinned: bool
    seller_name: str
    seller_url: str
    seller_rates: str
    image: str
    watch_id: int
    active: bool = True
    prev_prices: List[int] = field(default_factory=list)
    price_alert: bool = False
    
    @classmethod
    def create_new(cls, data: Dict[str, Any], watch_id: int) -> "Advertisement":
        """Create a new advertisement from scraper data."""
        return cls(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            price=data["price"],
            city=data["city"],
            date=data["date"],
            pinned=data["pinned"],
            seller_name=data["seller_name"],
            seller_url=data["seller_url"],
            seller_rates=data["seller_rates"],
            image=data["image"],
            watch_id=watch_id,
            active=True,
            prev_prices=[],
            price_alert=False
        )
    
    def has_price_changed(self, new_price: Optional[int]) -> bool:
        """Check if price has changed from current price."""
        if new_price is None:
            return False
        return self.price != new_price
    
    def update_price(self, new_price: Optional[int]) -> bool:
        """Update price and track price history. Returns True if price changed."""
        if not self.has_price_changed(new_price):
            return False
        
        if self.price is not None:
            self.prev_prices.append(self.price)
        
        self.price = new_price
        self.active = True  # Reactivate if it was inactive
        return True
    
    def deactivate(self) -> None:
        """Mark advertisement as inactive (no longer listed)."""
        self.active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "price": self.price,
            "city": self.city,
            "date": self.date,
            "pinned": self.pinned,
            "seller_name": self.seller_name,
            "seller_url": self.seller_url,
            "seller_rates": self.seller_rates,
            "image": self.image,
            "watch_id": self.watch_id,
            "active": self.active,
            "prev_prices": self.prev_prices,
            "price_alert": self.price_alert
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Advertisement":
        """Create from dictionary from persistence."""
        return cls(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            price=data["price"],
            city=data["city"],
            date=data["date"],
            pinned=data["pinned"],
            seller_name=data["seller_name"],
            seller_url=data["seller_url"],
            seller_rates=data["seller_rates"],
            image=data["image"],
            watch_id=data["watch_id"],
            active=data["active"],
            prev_prices=data["prev_prices"],
            price_alert=data["price_alert"]
        )