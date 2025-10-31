"""
Integration adapters for PYHABOT.

This package contains adapter implementations for various chat platforms
and notification services, implementing the NotifierPort and MessagePort interfaces.
"""

from typing import TYPE_CHECKING

from .base import IntegrationAdapter, MessageAdapter
from .discord import DiscordAdapter
from .telegram import TelegramAdapter
from .terminal import TerminalAdapter

if TYPE_CHECKING:
    from ...config import Config

__all__ = [
    "IntegrationAdapter",
    "MessageAdapter", 
    "DiscordAdapter",
    "TelegramAdapter",
    "TerminalAdapter",
    "create_integration",
]


async def create_integration(integration_name: str, config: "Config") -> IntegrationAdapter:
    """Factory function to create integration instances."""
    if integration_name == "discord":
        return DiscordAdapter(config.discord_token)
    elif integration_name == "telegram":
        return TelegramAdapter(config.telegram_token)
    elif integration_name == "terminal":
        return TerminalAdapter("")  # Terminal doesn't need a token
    else:
        raise ValueError(f"Unknown integration: {integration_name}")