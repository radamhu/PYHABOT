"""
Simplified Command Line Interface for PYHABOT.

This module provides a streamlined CLI without the integration pattern,
focused on core functionality: watch management and scraping.
"""

import argparse
import asyncio
import sys
from typing import Optional

from .simple_app import SimplePyhabot
from .simple_config import SimpleConfig as Config
from .logging import get_logger

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pyhabot",
        description="Simple async Python bot for monitoring HardverApró classified ads",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command - starts the background scraping
    run_parser = subparsers.add_parser(
        "run",
        help="Run the bot (starts background scraping)"
    )
    
    # Add watch command
    add_parser = subparsers.add_parser(
        "add-watch",
        help="Add a new watch URL"
    )
    add_parser.add_argument(
        "url",
        help="HardverApró search URL to watch"
    )
    
    # List watches command
    list_parser = subparsers.add_parser(
        "list",
        help="List all configured watches"
    )
    
    # Remove watch command
    remove_parser = subparsers.add_parser(
        "remove",
        help="Remove a watch by ID"
    )
    remove_parser.add_argument(
        "watch_id",
        type=int,
        help="ID of the watch to remove"
    )
    
    # Set webhook command
    webhook_parser = subparsers.add_parser(
        "set-webhook",
        help="Set webhook URL for a watch"
    )
    webhook_parser.add_argument(
        "watch_id",
        type=int,
        help="ID of the watch"
    )
    webhook_parser.add_argument(
        "webhook_url",
        help="Webhook URL to send notifications to"
    )
    
    # Force rescrape command
    rescrape_parser = subparsers.add_parser(
        "rescrape",
        help="Force re-scraping for a watch"
    )
    rescrape_parser.add_argument(
        "watch_id",
        type=int,
        help="ID of the watch to re-scrape"
    )
    
    return parser


async def run_command(config: Config) -> int:
    """Run the bot (start background scraping)."""
    try:
        bot = SimplePyhabot(config)
        
        print("🚀 Starting PYHABOT...")
        print("📊 Background scraping is now active")
        print("💡 Use Ctrl+C to stop the bot")
        print("🔧 Use 'pyhabot list' in another terminal to manage watches")
        print()
        
        await bot.start()
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down PYHABOT...")
        return 0
    except Exception as e:
        logger.error(f"Failed to run bot: {e}")
        print(f"❌ Error: {e}")
        return 1


async def add_watch_command(config: Config, url: str) -> int:
    """Add a new watch."""
    try:
        bot = SimplePyhabot(config)
        await bot.add_watch(url)
        return 0
    except Exception as e:
        logger.error(f"Failed to add watch: {e}")
        print(f"❌ Error: {e}")
        return 1


async def list_watches_command(config: Config) -> int:
    """List all watches."""
    try:
        bot = SimplePyhabot(config)
        await bot.list_watches()
        return 0
    except Exception as e:
        logger.error(f"Failed to list watches: {e}")
        print(f"❌ Error: {e}")
        return 1


async def remove_watch_command(config: Config, watch_id: int) -> int:
    """Remove a watch."""
    try:
        bot = SimplePyhabot(config)
        await bot.remove_watch(watch_id)
        return 0
    except Exception as e:
        logger.error(f"Failed to remove watch: {e}")
        print(f"❌ Error: {e}")
        return 1


async def set_webhook_command(config: Config, watch_id: int, webhook_url: str) -> int:
    """Set webhook for a watch."""
    try:
        bot = SimplePyhabot(config)
        await bot.set_webhook(watch_id, webhook_url)
        return 0
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        print(f"❌ Error: {e}")
        return 1


async def rescrape_command(config: Config, watch_id: int) -> int:
    """Force re-scraping for a watch."""
    try:
        bot = SimplePyhabot(config)
        await bot.force_rescrape(watch_id)
        return 0
    except Exception as e:
        logger.error(f"Failed to force rescrape: {e}")
        print(f"❌ Error: {e}")
        return 1


async def main_async(args: Optional[list[str]] = None) -> int:
    """Main async entry point."""
    try:
        # Load configuration
        config = Config()
        
        # Parse arguments
        parser = create_parser()
        parsed_args = parser.parse_args(args)
        
        # Handle commands
        if parsed_args.command == "run":
            return await run_command(config)
        elif parsed_args.command == "add-watch":
            return await add_watch_command(config, parsed_args.url)
        elif parsed_args.command == "list":
            return await list_watches_command(config)
        elif parsed_args.command == "remove":
            return await remove_watch_command(config, parsed_args.watch_id)
        elif parsed_args.command == "set-webhook":
            return await set_webhook_command(config, parsed_args.watch_id, parsed_args.webhook_url)
        elif parsed_args.command == "rescrape":
            return await rescrape_command(config, parsed_args.watch_id)
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        print(f"❌ Error: {e}")
        return 1


def main(args: Optional[list[str]] = None) -> int:
    """Synchronous wrapper for main_async."""
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())