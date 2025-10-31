"""
Base classes for integration adapters.

These classes provide the foundation for implementing platform-specific
integrations while conforming to the NotifierPort and MessagePort interfaces.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

from ...domain.models import NotificationTarget
from ...domain.ports import NotifierPort, MessagePort

logger = logging.getLogger(__name__)


class MessageAdapter(ABC):
    """Base adapter for handling messages from chat platforms."""
    
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
    
    # Utility methods for message formatting
    @staticmethod
    def split_to_chunks(text: str, size: int = 2000) -> list[str]:
        """Split text into chunks of specified size."""
        return [text[i:i + size] for i in range(0, len(text), size)]
    
    @staticmethod
    def format_hyperlink(text: str, url: str) -> str:
        """Format a hyperlink (platform-specific)."""
        return f"[{text}]({url})"
    
    @staticmethod
    def escape(text: str) -> str:
        """Escape special characters (platform-specific)."""
        return text
    
    @staticmethod
    def strikethrough(text: str) -> str:
        """Format text as strikethrough (platform-specific)."""
        return f"~~{text}~~"


class IntegrationAdapter(NotifierPort, ABC):
    """Base adapter for integration platforms."""
    
    def __init__(self, token: str):
        self.token = token
        self.on_message_callback = lambda *_: None
        self.on_ready_callback = lambda *_: None
        logger.info(f"Started with '{self.__class__.__name__}'!")
    
    def register_on_message_callback(self, callback) -> None:
        """Register callback for incoming messages."""
        self.on_message_callback = callback
    
    def register_on_ready_callback(self, callback) -> None:
        """Register callback for when integration is ready."""
        self.on_ready_callback = callback
    
    @property
    def name(self) -> str:
        """Get the integration name."""
        return self.__class__.__name__
    
    @abstractmethod
    def run(self) -> None:
        """Start the integration."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources and shutdown gracefully."""
        pass
    
    @abstractmethod
    async def send_message_to_channel(self, channel_id: str, text: str, no_preview: bool = False, **kwargs) -> bool:
        """
        Send a message to a channel.
        
        Args:
            channel_id: The channel ID
            text: The message text
            no_preview: Whether to disable link previews
            **kwargs: Additional platform-specific options
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    # NotifierPort implementation
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
        try:
            return await self.send_message_to_channel(
                target.channel_id, 
                message, 
                no_preview=no_preview, 
                **kwargs
            )
        except Exception as e:
            logger.error(f"Failed to send notification to {target.channel_id}: {e}")
            return False
    
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
        # Default implementation - should be overridden by platforms that support webhooks
        logger.warning(f"Webhook notifications not supported by {self.name}")
        return False
    
    def format_message(self, message_type: str, **kwargs) -> str:
        """
        Format a message according to message type.
        
        Args:
            message_type: Type of message (e.g., 'new_ad', 'price_change')
            **kwargs: Template variables
            
        Returns:
            Formatted message string
        """
        templates = {
            "new_ad": (
                "🆕 Új hirdetés: {title}\n"
                "💰 Ár: {price} Ft\n"
                "📍 Helyszín: {city}\n"
                "👤 Eladó: {seller_name}\n"
                "🔗 {url}"
            ),
            "price_change": (
                "💸 Árváltozás: {title}\n"
                "📉 Régi ár: {old_price} Ft\n"
                "📈 Új ár: {new_price} Ft\n"
                "📍 Helyszín: {city}\n"
                "🔗 {url}"
            ),
            "error": "❌ Hiba történt: {error}",
            "info": "ℹ️ {message}",
            "success": "✅ {message}"
        }
        
        template = templates.get(message_type, "{message}")
        
        # Format price values
        if "price" in kwargs and kwargs["price"] is not None:
            kwargs["price"] = f"{kwargs['price']:,}".replace(",", " ")
        if "old_price" in kwargs and kwargs["old_price"] is not None:
            kwargs["old_price"] = f"{kwargs['old_price']:,}".replace(",", " ")
        if "new_price" in kwargs and kwargs["new_price"] is not None:
            kwargs["new_price"] = f"{kwargs['new_price']:,}".replace(",", " ")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing template variable {e} for message type {message_type}")
            return f"Message formatting error: {e}"