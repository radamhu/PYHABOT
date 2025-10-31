"""
Telegram integration adapter for PYHABOT.

This adapter implements the IntegrationAdapter interface for Telegram,
providing both message handling and notification capabilities.
"""

import asyncio
import logging
import re
from typing import Optional

import telegrampy
from telegrampy.ext.commands import Bot as TelegramBot

from .base import IntegrationAdapter, MessageAdapter
from ...domain.models import NotificationTarget

logger = logging.getLogger(__name__)


class TelegramMessage(MessageAdapter):
    """Telegram message implementation."""
    
    def __init__(self, msg: telegrampy.Message):
        self._msg = msg
        self._client = None
        self._callback = None
    
    @property
    def text(self) -> str:
        return self._msg.content
    
    @property
    def channel_id(self) -> str:
        return str(self._msg.chat.id)
    
    async def handle_message(self, content: str, channel_id: str, user_id: str) -> Optional[str]:
        """Handle message through registered callback."""
        if self._callback:
            return await self._callback(content, channel_id, user_id)
        return None
    
    async def send_response(self, channel_id: str, response: str) -> bool:
        """Send response to Telegram chat."""
        try:
            if self._client:
                chat = await self._client.get_chat(int(channel_id))
                params = {
                    "chat_id": chat.id, 
                    "parse_mode": "Markdown"
                }
                
                for chunk in self.split_to_chunks(response, size=4000):
                    params["text"] = chunk
                    await self._client.http.request("sendMessage", json=params)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram response: {e}")
            return False
    
    async def send_back(self, text: str, no_preview: bool = False, **kwargs) -> None:
        """Send message back to same chat."""
        params = {
            "chat_id": self._msg.chat.id, 
            "parse_mode": "Markdown", 
            **kwargs
        }
        if no_preview:
            params["disable_web_page_preview"] = True
        
        for chunk in self.split_to_chunks(text, size=4000):
            params["text"] = chunk
            await self._msg._http.request("sendMessage", json=params)
    
    async def reply(self, text: str, **kwargs) -> None:
        """Reply to original message."""
        for chunk in self.split_to_chunks(text, size=4000):
            await self._msg.reply(chunk, parse_mode="Markdown", **kwargs)
    
    @staticmethod
    def split_to_chunks(text: str, size: int = 4000) -> list[str]:
        """Split text into chunks for Telegram (max 4096 chars)."""
        return MessageAdapter.split_to_chunks(text, size)
    
    @staticmethod
    def escape(text: str) -> str:
        """Escape Telegram markdown characters."""
        # Telegram V2 markdown requires escaping _*~` characters
        _special_chars_map = {i: "\\" + chr(i) for i in b"_*~`"}
        
        # Regex pattern to find inline (`code`) and multiline (```code```) code blocks
        pattern = r"(```.*?```|`[^`\n]*`)"
        
        # List to store parts of final result
        parts = []
        last_end = 0
        
        # Iterate through all code blocks
        for match in re.finditer(pattern, text, re.DOTALL):
            start, end = match.span()
            # Escape text outside code blocks
            parts.append(text[last_end:start].translate(_special_chars_map))
            # Keep code block unchanged
            parts.append(text[start:end])
            last_end = end
        
        # Add remaining text after last code block
        parts.append(text[last_end:].translate(_special_chars_map))
        
        return "".join(parts)


class TelegramAdapter(IntegrationAdapter, TelegramBot):
    """Telegram integration adapter."""
    
    def __init__(self, token: str):
        # Initialize Telegram bot
        TelegramBot.__init__(self, token)
        
        # Initialize integration adapter
        IntegrationAdapter.__init__(self, token)
        
        self._message_handler = None
        self.event(self.on_message)
    
    def register_on_message_callback(self, callback) -> None:
        """Register callback for incoming messages."""
        super().register_on_message_callback(callback)
        self._message_handler = callback
    
    async def on_message(self, message: telegrampy.Message) -> None:
        """Handle incoming Telegram messages."""
        if self._message_handler:
            telegram_msg = TelegramMessage(message)
            telegram_msg._client = self
            telegram_msg._callback = self._message_handler
            
            try:
                await self._message_handler(
                    telegram_msg.text,
                    telegram_msg.channel_id,
                    str(message.author.id) if message.author else "unknown"
                )
            except Exception as e:
                logger.error(f"Error handling Telegram message: {e}")
    
    def run(self) -> None:
        """Start the Telegram bot."""
        try:
            # Schedule ready callback
            asyncio.get_event_loop().create_task(self.on_ready_callback())
            super().run()
        except Exception as e:
            logger.error(f"Telegram bot failed to start: {e}")
            raise
    
    async def send_message_to_channel(
        self, 
        channel_id: str, 
        text: str, 
        no_preview: bool = False, 
        **kwargs
    ) -> bool:
        """Send a message to a Telegram chat."""
        try:
            chat = await self.get_chat(int(channel_id))
            params = {
                "chat_id": chat.id, 
                "parse_mode": "Markdown", 
                **kwargs
            }
            
            if no_preview:
                params["disable_web_page_preview"] = True
            
            for chunk in TelegramMessage.split_to_chunks(text, size=4000):
                params["text"] = chunk
                await self.http.request("sendMessage", json=params)
            
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {channel_id}: {e}")
            return False
    
    def format_message(self, message_type: str, **kwargs) -> str:
        """Format message for Telegram with proper escaping."""
        base_message = super().format_message(message_type, **kwargs)
        
        # Apply Telegram-specific formatting and escaping
        if message_type in ["new_ad", "price_change"]:
            return TelegramMessage.escape(base_message)
        
        return base_message
    
    async def cleanup(self) -> None:
        """Clean up Telegram bot resources."""
        try:
            if hasattr(self, 'http') and self.http:
                await self.http.close()
            logger.info("Telegram bot cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Telegram bot: {e}")