"""
Discord integration adapter for PYHABOT.

This adapter implements the IntegrationAdapter interface for Discord,
providing both message handling and notification capabilities.
"""

import logging
from typing import Optional

import discord

from .base import IntegrationAdapter, MessageAdapter
from ...domain.models import NotificationTarget

logger = logging.getLogger(__name__)


class DiscordMessage(MessageAdapter):
    """Discord message implementation."""
    
    def __init__(self, msg: discord.Message):
        self._msg = msg
    
    @property
    def text(self) -> str:
        return self._msg.content
    
    @property
    def channel_id(self) -> str:
        return str(self._msg.channel.id)
    
    async def handle_message(self, content: str, channel_id: str, user_id: str) -> Optional[str]:
        """Handle message through registered callback."""
        return await self._callback(content, channel_id, user_id)
    
    async def send_response(self, channel_id: str, response: str) -> bool:
        """Send response to Discord channel."""
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                for chunk in self.split_to_chunks(response):
                    await channel.send(chunk)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to send Discord response: {e}")
            return False
    
    async def send_back(self, text: str, no_preview: bool = False, **kwargs) -> discord.Message:
        """Send message back to the same channel."""
        message = await self._msg.channel.send(text)
        if no_preview:
            await message.edit(suppress=True)
        return message
    
    async def reply(self, text: str) -> discord.Message:
        """Reply to the original message."""
        return await self._msg.reply(text)
    
    @staticmethod
    def escape(text: str) -> str:
        """Escape Discord markdown."""
        # Basic Discord markdown escaping
        escape_chars = ['\\', '`', '*', '_', '~', '|']
        for char in escape_chars:
            text = text.replace(char, '\\' + char)
        return text


class DiscordAdapter(IntegrationAdapter, discord.Client):
    """Discord integration adapter."""
    
    def __init__(self, token: str):
        # Initialize Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        discord.Client.__init__(self, intents=intents)
        
        # Initialize integration adapter
        IntegrationAdapter.__init__(self, token)
        
        self._message_handler = None
    
    def register_on_message_callback(self, callback) -> None:
        """Register callback for incoming messages."""
        super().register_on_message_callback(callback)
        self._message_handler = callback
    
    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming Discord messages."""
        if not message.author.bot and self._message_handler:
            discord_msg = DiscordMessage(message)
            discord_msg._client = self
            discord_msg._callback = self._message_handler
            
            try:
                await self._message_handler(
                    discord_msg.text,
                    discord_msg.channel_id,
                    str(message.author.id)
                )
            except Exception as e:
                logger.error(f"Error handling Discord message: {e}")
    
    async def on_ready(self) -> None:
        """Handle Discord client ready event."""
        await self.on_ready_callback()
        
        # Set bot activity
        try:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching, 
                    name="HardverApró"
                )
            )
        except Exception as e:
            logger.warning(f"Failed to set Discord activity: {e}")
        
        # Log invite link
        if self.user:
            invite_link = (
                f"https://discord.com/oauth2/authorize?"
                f"client_id={self.user.id}&scope=bot&permissions=8"
            )
            logger.info(f"Discord bot ready. Invite link: {invite_link}")
    
    def run(self) -> None:
        """Start the Discord bot."""
        try:
            super().run(self.token)
        except Exception as e:
            logger.error(f"Discord bot failed to start: {e}")
            raise
    
    async def send_message_to_channel(
        self, 
        channel_id: str, 
        text: str, 
        no_preview: bool = False, 
        **kwargs
    ) -> bool:
        """Send a message to a Discord channel."""
        try:
            channel = self.get_channel(int(channel_id))
            if not channel:
                logger.warning(f"Discord channel {channel_id} not found")
                return False
            
            for chunk in DiscordMessage.split_to_chunks(text):
                message = await channel.send(chunk)
                if no_preview:
                    await message.edit(suppress=True)
            
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord message to {channel_id}: {e}")
            return False
    
    def format_message(self, message_type: str, **kwargs) -> str:
        """Format message for Discord with proper escaping."""
        base_message = super().format_message(message_type, **kwargs)
        
        # Apply Discord-specific formatting
        if message_type in ["new_ad", "price_change"]:
            # Use Discord embeds for better formatting
            # For now, just ensure proper escaping
            return DiscordMessage.escape(base_message)
        
        return base_message
    
    async def cleanup(self) -> None:
        """Clean up Discord client resources."""
        try:
            if self.is_ready():
                await self.close()
            logger.info("Discord client cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Discord client: {e}")