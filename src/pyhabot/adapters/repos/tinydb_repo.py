"""
TinyDB repository adapter for PYHABOT.

This adapter implements the RepoPort interface using TinyDB for persistence.
It maintains compatibility with the existing JSON schema and doc_id behavior.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from tinydb import Query, TinyDB
from tinydb.table import Document

from ...domain.models import Watch, Advertisement
from ...domain.ports import RepoPort


class TinyDBRepository(RepoPort):
    """TinyDB implementation of the repository port."""
    
    def __init__(self, folder: Path | str, filename: str = "watchlist.json"):
        folder = Path(folder)
        folder.mkdir(exist_ok=True)
        self.db = TinyDB(folder / filename)
        self.watchlist = self.db.table("watchlist")
        self.advertisements = self.db.table("advertisements")
    
    # Watch operations
    def get_watch(self, watch_id: int) -> Optional[Watch]:
        """Get a watch by ID."""
        doc = self.watchlist.get(doc_id=watch_id)
        if doc:
            return Watch.from_dict(doc)
        return None
    
    def get_all_watches(self) -> List[Watch]:
        """Get all watches."""
        return [Watch.from_dict(doc) for doc in self.watchlist.all()]
    
    def add_watch(self, url: str) -> int:
        """Add a new watch and return its ID."""
        doc_id = self.watchlist.insert({
            "url": url,
            "last_checked": 0.0,
            "notifyon": None,
            "webhook": None
        })
        # Add the ID to the document for compatibility
        self.watchlist.update({"id": doc_id}, doc_ids=[doc_id])
        return doc_id
    
    def remove_watch(self, watch_id: int) -> bool:
        """Remove a watch by ID. Returns True if successful."""
        try:
            self.watchlist.remove(doc_ids=[watch_id])
            self.clear_advertisements_for_watch(watch_id)
            return True
        except Exception:
            return False
    
    def update_watch(self, watch: Watch) -> bool:
        """Update a watch. Returns True if successful."""
        try:
            self.watchlist.update(watch.to_dict(), doc_ids=[watch.id])
            return True
        except Exception:
            return False
    
    def get_watches_needing_check(self, check_interval: int) -> List[Watch]:
        """Get watches that need to be checked based on interval."""
        WatchQuery = Query()
        threshold = int(datetime.now().timestamp()) - check_interval
        docs = self.watchlist.search(WatchQuery.last_checked < threshold)
        return [Watch.from_dict(doc) for doc in docs]
    
    def clear_advertisements_for_watch(self, watch_id: int) -> bool:
        """Clear all advertisements for a given watch."""
        try:
            AdQuery = Query()
            self.advertisements.remove(AdQuery.watch_id == watch_id)
            return True
        except Exception:
            return False
    
    # Advertisement operations
    def get_advertisement(self, ad_id: int) -> Optional[Advertisement]:
        """Get an advertisement by ID."""
        doc = self.advertisements.get(doc_id=ad_id)
        if doc:
            return Advertisement.from_dict(doc)
        return None
    
    def add_advertisement(self, ad_data: Dict[str, Any], watch_id: int) -> Advertisement:
        """Add a new advertisement."""
        ad_id = ad_data["id"]
        
        # Create the advertisement document with TinyDB compatibility
        doc = Document(
            {
                **ad_data,
                "prev_prices": [],
                "watch_id": watch_id,
                "active": True,
                "price_alert": False
            },
            doc_id=ad_id
        )
        
        self.advertisements.insert(doc)
        return Advertisement.from_dict(doc)
    
    def update_advertisement(self, ad_data: Dict[str, Any]) -> bool:
        """
        Update an advertisement with new data.
        Returns True if price changed, False otherwise.
        """
        ad_id = ad_data["id"]
        doc = self.advertisements.get(doc_id=ad_id)
        
        if doc is None:
            return False
        
        # Reactivate if it was inactive
        self.advertisements.update({"active": True}, doc_ids=[ad_id])
        
        # Check if price changed
        if doc["price"] != ad_data["price"]:
            # Add current price to history
            current_prices = doc.get("prev_prices", [])
            if doc["price"] is not None:
                current_prices.append(doc["price"])
            
            self.advertisements.update(
                {"prev_prices": current_prices},
                doc_ids=[ad_id]
            )
            
            # Update the price
            self.advertisements.update(
                {"price": ad_data["price"]},
                doc_ids=[ad_id]
            )
            
            return True
        
        return False
    
    def set_advertisement_price_alert(self, ad_id: int, enabled: bool) -> bool:
        """Enable or disable price alerts for an advertisement."""
        try:
            self.advertisements.update({"price_alert": enabled}, doc_ids=[ad_id])
            return True
        except Exception:
            return False
    
    def set_advertisement_inactive(self, ad_id: int) -> bool:
        """Mark an advertisement as inactive."""
        try:
            self.advertisements.update({"active": False}, doc_ids=[ad_id])
            return True
        except Exception:
            return False
    
    def get_active_advertisements(self, watch_id: int) -> List[Advertisement]:
        """Get all active advertisements for a watch."""
        AdQuery = Query()
        docs = self.advertisements.search(
            (AdQuery.watch_id == watch_id) & (AdQuery.active == True)
        )
        return [Advertisement.from_dict(doc) for doc in docs]
    
    def get_inactive_advertisements(self, watch_id: int) -> List[Advertisement]:
        """Get all inactive advertisements for a watch."""
        AdQuery = Query()
        docs = self.advertisements.search(
            (AdQuery.watch_id == watch_id) & (AdQuery.active == False)
        )
        return [Advertisement.from_dict(doc) for doc in docs]
    
    def get_all_advertisements(self, watch_id: int) -> List[Advertisement]:
        """Get all advertisements for a watch."""
        AdQuery = Query()
        docs = self.advertisements.search(AdQuery.watch_id == watch_id)
        return [Advertisement.from_dict(doc) for doc in docs]
    
    # Legacy compatibility methods (can be removed after full migration)
    def reset_watch_last_checked(self, watch_id: int) -> None:
        """Legacy method: reset watch last_checked time."""
        self.watchlist.update({"last_checked": 0.0}, doc_ids=[watch_id])
    
    def reset_all_watch_last_checked(self) -> None:
        """Legacy method: reset all watches last_checked time."""
        self.watchlist.update({"last_checked": 0.0})
    
    def set_watch_url(self, watch_id: int, url: str) -> None:
        """Legacy method: set watch URL."""
        self.watchlist.update({"url": url}, doc_ids=[watch_id])
    
    def set_watch_notifyon(self, watch_id: int, channel_id: str, integration_name: str) -> None:
        """Legacy method: set watch notification target."""
        self.watchlist.update(
            {"notifyon": {"channel_id": channel_id, "integration": integration_name}},
            doc_ids=[watch_id],
        )
    
    def set_watch_lastchecked(self, watch_id: int) -> None:
        """Legacy method: mark watch as checked."""
        self.watchlist.update({"last_checked": datetime.now().timestamp()}, doc_ids=[watch_id])
    
    def clear_watch_notifyon(self, watch_id: int) -> None:
        """Legacy method: clear watch notification target."""
        self.watchlist.update({"notifyon": None}, doc_ids=[watch_id])
    
    def set_watch_webhook(self, watch_id: int, webhook: str) -> None:
        """Legacy method: set watch webhook."""
        self.watchlist.update({"webhook": webhook}, doc_ids=[watch_id])
    
    def clear_watch_webhook(self, watch_id: int) -> None:
        """Legacy method: clear watch webhook."""
        self.watchlist.update({"webhook": None}, doc_ids=[watch_id])
    
    def remove_advertisement(self, ad_id: int) -> None:
        """Legacy method: remove advertisement."""
        self.advertisements.remove(doc_ids=[ad_id])
    
    def clear_all_advertisements(self) -> None:
        """Legacy method: clear all advertisements."""
        self.advertisements.truncate()