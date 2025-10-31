"""
Adapters for PYHABOT.

This package contains adapter implementations that connect the domain logic
to external systems like databases, scrapers, and notification services.
"""

from .repos.tinydb_repo import TinyDBRepository
from .scraping.hardverapro import HardveraproScraper
from .integrations.base import IntegrationAdapter, MessageAdapter
from .integrations.discord import DiscordAdapter
from .integrations.telegram import TelegramAdapter
from .integrations.terminal import TerminalAdapter
from .notifications.webhook import WebhookNotifier

__all__ = [
    "TinyDBRepository",
    "HardveraproScraper",
    "IntegrationAdapter",
    "MessageAdapter",
    "DiscordAdapter", 
    "TelegramAdapter",
    "TerminalAdapter",
    "WebhookNotifier",
]