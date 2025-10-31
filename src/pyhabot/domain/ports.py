"""
Port definitions for PYHABOT.

Ports define the contracts that adapters must implement to interact with external systems.
This follows the Hexagonal Architecture pattern where business logic depends on abstractions.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator
from .models import Watch, Advertisement, NotificationTarget


class ScraperPort(ABC):
    """Port for scraping advertisements from external sources."""
    
    @abstractmethod
    async def scrape_ads(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape advertisements from a given URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            List of advertisement data dictionaries
            
        Raises:
            NetworkError: If scraping fails due to network issues
            ParseError: If parsing the scraped content fails
        """
        pass
    
    @abstractmethod
    async def check_robots_txt(self, base_url: str) -> bool:
        """
        Check if scraping is allowed by robots.txt.
        
        Args:
            base_url: Base URL to check robots.txt for
            
        Returns:
            True if scraping is allowed, False otherwise
        """
        pass


class RepoPort(ABC):
    """Port for data persistence operations."""
    
    # Watch operations
    @abstractmethod
    def get_watch(self, watch_id: int) -> Optional[Watch]:
        """Get a watch by ID."""
        pass
    
    @abstractmethod
    def get_all_watches(self) -> List[Watch]:
        """Get all watches."""
        pass
    
    @abstractmethod
    def add_watch(self, url: str) -> int:
        """Add a new watch and return its ID."""
        pass
    
    @abstractmethod
    def remove_watch(self, watch_id: int) -> bool:
        """Remove a watch by ID. Returns True if successful."""
        pass
    
    @abstractmethod
    def update_watch(self, watch: Watch) -> bool:
        """Update a watch. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_watches_needing_check(self, check_interval: int) -> List[Watch]:
        """Get watches that need to be checked based on interval."""
        pass
    
    @abstractmethod
    def clear_advertisements_for_watch(self, watch_id: int) -> bool:
        """Clear all advertisements for a given watch."""
        pass
    
    # Advertisement operations
    @abstractmethod
    def get_advertisement(self, ad_id: int) -> Optional[Advertisement]:
        """Get an advertisement by ID."""
        pass
    
    @abstractmethod
    def add_advertisement(self, ad_data: Dict[str, Any], watch_id: int) -> Advertisement:
        """Add a new advertisement."""
        pass
    
    @abstractmethod
    def update_advertisement(self, ad_data: Dict[str, Any]) -> bool:
        """
        Update an advertisement with new data.
        Returns True if price changed, False otherwise.
        """
        pass
    
    @abstractmethod
    def set_advertisement_price_alert(self, ad_id: int, enabled: bool) -> bool:
        """Enable or disable price alerts for an advertisement."""
        pass
    
    @abstractmethod
    def set_advertisement_inactive(self, ad_id: int) -> bool:
        """Mark an advertisement as inactive."""
        pass
    
    @abstractmethod
    def get_active_advertisements(self, watch_id: int) -> List[Advertisement]:
        """Get all active advertisements for a watch."""
        pass
    
    @abstractmethod
    def get_inactive_advertisements(self, watch_id: int) -> List[Advertisement]:
        """Get all inactive advertisements for a watch."""
        pass
    
    @abstractmethod
    def get_all_advertisements(self, watch_id: int) -> List[Advertisement]:
        """Get all advertisements for a watch."""
        pass


class NotifierPort(ABC):
    """Port for sending notifications through various channels."""
    
    @abstractmethod
    async def send_notification(
        self, 
        target: NotificationTarget, 
        message: str, 
        no_preview: bool = False,
        **kwargs
    ) -> bool:
        """
        Send a notification to a target.
        
        Args:
            target: The notification target
            message: The message to send
            no_preview: Whether to disable link previews
            **kwargs: Additional platform-specific options
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def send_webhook_notification(
        self, 
        webhook_url: str, 
        message: str, 
        **kwargs
    ) -> bool:
        """
        Send a notification via webhook.
        
        Args:
            webhook_url: The webhook URL
            message: The message to send
            **kwargs: Additional webhook-specific options
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def format_message(self, message_type: str, **kwargs) -> str:
        """
        Format a message according to the message type.
        
        Args:
            message_type: Type of message (e.g., 'new_ad', 'price_change')
            **kwargs: Template variables
            
        Returns:
            Formatted message string
        """
        pass


class MessagePort(ABC):
    """Port for handling incoming messages from chat platforms."""
    
    @abstractmethod
    async def handle_message(self, content: str, channel_id: str, user_id: str) -> Optional[str]:
        """
        Handle an incoming message.
        
        Args:
            content: The message content
            channel_id: The channel ID
            user_id: The user ID
            
        Returns:
            Response message if any, None otherwise
        """
        pass
    
    @abstractmethod
    async def send_response(self, channel_id: str, response: str) -> bool:
        """
        Send a response to a channel.
        
        Args:
            channel_id: The channel ID to send to
            response: The response message
            
        Returns:
            True if successful, False otherwise
        """
        pass