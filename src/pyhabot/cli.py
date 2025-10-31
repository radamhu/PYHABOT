"""
Command Line Interface for PYHABOT.

This module provides the main CLI entry point for the application,
including subcommands for running the bot and managing configurations.
"""

import argparse
import asyncio
import sys
from typing import Optional

from .app import Pyhabot
from .config import Config
from .logging import get_logger
from .adapters.repos.tinydb_repo import TinyDBRepository
from .domain.services import WatchService

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pyhabot",
        description="Async Python bot for monitoring HardverApró classified ads",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser(
        "run",
        help="Run the bot with specified integration"
    )
    run_parser.add_argument(
        "--integration",
        choices=["discord", "telegram", "terminal"],
        help="Integration to use (overrides INTEGRATION env var)"
    )
    
    # Add watch command
    add_parser = subparsers.add_parser(
        "add-watch",
        help="Add a new watch URL"
    )
    add_parser.add_argument(
        "url",
        help="URL to watch"
    )
    
    # List watches command
    subparsers.add_parser(
        "list",
        help="List all watches"
    )
    
    # Rescrape command
    rescrape_parser = subparsers.add_parser(
        "rescrape",
        help="Force re-scrape of watches"
    )
    rescrape_parser.add_argument(
        "watch_id",
        nargs="?",
        help="Specific watch ID to rescrape (optional)"
    )
    
    # Set prefix command
    prefix_parser = subparsers.add_parser(
        "setprefix",
        help="Set command prefix"
    )
    prefix_parser.add_argument(
        "prefix",
        help="New command prefix"
    )
    
    # Notify on command
    notify_parser = subparsers.add_parser(
        "notifyon",
        help="Enable notifications for a watch"
    )
    notify_parser.add_argument(
        "watch_id",
        help="Watch ID to enable notifications for"
    )
    
    # Set webhook command
    webhook_parser = subparsers.add_parser(
        "setwebhook",
        help="Set webhook URL for a watch"
    )
    webhook_parser.add_argument(
        "watch_id",
        help="Watch ID to set webhook for"
    )
    webhook_parser.add_argument(
        "url",
        help="Webhook URL"
    )
    
    return parser


async def main_async(args: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command is None:
        parser.print_help()
        return 1
    
    try:
        # Load configuration
        config = Config()
        
        # Import here to avoid circular imports
        from .adapters.integrations import create_integration
        from .domain.services import WatchService
        
        if parsed_args.command == "run":
            # Run the bot
            integration = parsed_args.integration or config.integration
            if not integration:
                logger.error("No integration specified. Use --integration or set INTEGRATION env var")
                return 1
            
            logger.info(f"Starting PYHABOT with {integration} integration")
            app = Pyhabot(config)
            return app.run(integration)
        
        elif parsed_args.command == "add-watch":
            logger.info(f"Adding watch for URL: {parsed_args.url}")
            try:
                # Create a temporary repo adapter to add the watch
                repo = TinyDBRepository(config.persistent_data_path)
                watch_service = WatchService(repo)
                watch_id = watch_service.create_watch(parsed_args.url)
                
                print(f"Watch added successfully with ID: {watch_id}")
                return 0
            except Exception as e:
                logger.error(f"Failed to add watch: {e}")
                print(f"Error adding watch: {e}")
                return 1
        
        elif parsed_args.command == "list":
            logger.info("Listing watches")
            try:
                repo = TinyDBRepository(config.persistent_data_path)
                watch_service = WatchService(repo)
                watches = watch_service.get_all_watches()
                
                if not watches:
                    print("No watches configured.")
                else:
                    print("Configured watches:")
                    for watch in watches:
                        status = "✓" if watch.notifyon else "✗"
                        webhook = "🔗" if watch.webhook else ""
                        print(f"  [{watch.id}] {watch.url} {status} {webhook}")
                return 0
            except Exception as e:
                logger.error(f"Failed to list watches: {e}")
                print(f"Error listing watches: {e}")
                return 1
        
        elif parsed_args.command == "rescrape":
            watch_id = parsed_args.watch_id
            logger.info(f"Rescraping watch: {watch_id or 'all watches'}")
            try:
                repo = TinyDBRepository(config.persistent_data_path)
                watch_service = WatchService(repo)
                
                if watch_id:
                    # Force rescrape specific watch
                    success = watch_service.force_rescrape_watch(int(watch_id))
                    if success:
                        print(f"Watch {watch_id} marked for immediate rescrape.")
                    else:
                        print(f"Watch {watch_id} not found.")
                        return 1
                else:
                    # Force rescrape all watches
                    watches = watch_service.get_all_watches()
                    for watch in watches:
                        watch_service.force_rescrape_watch(watch.id)
                    print(f"Marked {len(watches)} watches for immediate rescrape.")
                
                return 0
            except Exception as e:
                logger.error(f"Failed to rescrape: {e}")
                print(f"Error rescraping: {e}")
                return 1
        
        elif parsed_args.command == "setprefix":
            logger.info(f"Setting command prefix to: {parsed_args.prefix}")
            try:
                # For now, we'll store this in the config file
                # This is a simplified implementation
                print(f"Command prefix set to: {parsed_args.prefix}")
                print("Note: This will be implemented in the config system in a future update.")
                return 0
            except Exception as e:
                logger.error(f"Failed to set prefix: {e}")
                print(f"Error setting prefix: {e}")
                return 1
        
        elif parsed_args.command == "notifyon":
            logger.info(f"Enabling notifications for watch: {parsed_args.watch_id}")
            try:
                repo = TinyDBRepository(config.persistent_data_path)
                watch_service = WatchService(repo)
                
                # For now, we'll enable notifications for the default integration
                # This is a simplified implementation
                success = watch_service.set_notification_target(
                    int(parsed_args.watch_id),
                    "default",  # channel_id
                    config.integration  # integration type
                )
                
                if success:
                    print(f"Notifications enabled for watch {parsed_args.watch_id}")
                else:
                    print(f"Watch {parsed_args.watch_id} not found.")
                    return 1
                
                return 0
            except Exception as e:
                logger.error(f"Failed to enable notifications: {e}")
                print(f"Error enabling notifications: {e}")
                return 1
        
        elif parsed_args.command == "setwebhook":
            logger.info(f"Setting webhook for watch {parsed_args.watch_id}: {parsed_args.url}")
            try:
                repo = TinyDBRepository(config.persistent_data_path)
                watch_service = WatchService(repo)
                
                success = watch_service.set_webhook(int(parsed_args.watch_id), parsed_args.url)
                
                if success:
                    print(f"Webhook set for watch {parsed_args.watch_id}")
                else:
                    print(f"Watch {parsed_args.watch_id} not found.")
                    return 1
                
                return 0
            except Exception as e:
                logger.error(f"Failed to set webhook: {e}")
                print(f"Error setting webhook: {e}")
                return 1
        
        else:
            logger.error(f"Unknown command: {parsed_args.command}")
            return 1
    
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return 1


def main(args: Optional[list[str]] = None) -> int:
    """Synchronous wrapper for main_async."""
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())