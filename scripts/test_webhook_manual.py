#!/usr/bin/env python3
"""
Manual webhook testing script.

This script allows manual testing of webhook functionality
with different webhook types and configurations.
"""

import asyncio
import argparse
import json
import sys
from typing import Optional

import aiohttp

# Add src to path for imports
sys.path.insert(0, 'src')

from src.pyhabot.adapters.notifications.webhook import WebhookNotifier


async def test_webhook(
    webhook_url: str,
    message: str,
    webhook_type: str = "generic",
    username: Optional[str] = None,
    avatar_url: Optional[str] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    verbose: bool = False
):
    """Test a webhook with the given parameters."""
    
    print(f"Testing webhook: {webhook_url}")
    print(f"Type: {webhook_type}")
    print(f"Message: {message}")
    print(f"Max retries: {max_retries}")
    print("-" * 50)
    
    # Prepare webhook options
    webhook_options = {
        "webhook_type": webhook_type,
    }
    
    if username:
        webhook_options["username"] = username
    if avatar_url:
        webhook_options["avatar_url"] = avatar_url
    
    # Add Discord-specific embeds if Discord webhook
    if webhook_type == "discord":
        webhook_options["embeds"] = [{
            "title": "🆕 Új hirdetés értesítő",
            "description": message,
            "color": 0x00ff00,
            "fields": [
                {
                    "name": "Forrás",
                    "value": "PYHABOT",
                    "inline": True
                },
                {
                    "name": "Időpont",
                    "value": "<t:" + str(int(asyncio.get_event_loop().time())) + ":R>",
                    "inline": True
                }
            ],
            "footer": {
                "text": "PYHABOT - HardverApró figyelő"
            }
        }]
    
    # Add Slack-specific attachments if Slack webhook
    elif webhook_type == "slack":
        webhook_options["attachments"] = [{
            "color": "good",
            "title": "Új hirdetés értesítő",
            "text": message,
            "fields": [
                {
                    "title": "Forrás",
                    "value": "PYHABOT",
                    "short": True
                },
                {
                    "title": "Típus",
                    "value": "Webhook Teszt",
                    "short": True
                }
            ],
            "footer": "PYHABOT - HardverApró figyelő"
        }]
    
    async with aiohttp.ClientSession() as session:
        notifier = WebhookNotifier(
            session,
            max_retries=max_retries,
            base_delay=base_delay,
            jitter=True
        )
        
        if verbose:
            print("Webhook payload:")
            payload = notifier._prepare_payload(message, **webhook_options)
            print(json.dumps(payload, indent=2))
            print("-" * 50)
        
        print("Sending webhook notification...")
        success = await notifier.send_webhook_notification(
            webhook_url,
            message,
            **webhook_options
        )
        
        if success:
            print("✅ Webhook notification sent successfully!")
        else:
            print("❌ Webhook notification failed!")
            return False
    
    return True


async def test_discord_webhook():
    """Test Discord webhook with sample data."""
    webhook_url = input("Enter Discord webhook URL: ").strip()
    if not webhook_url:
        print("No webhook URL provided")
        return False
    
    return await test_webhook(
        webhook_url,
        "🆕 Új hirdetés: Eladó használt laptop\n💰 Ár: 150 000 Ft\n📍 Helyszín: Budapest\n👤 Eladó: János\n🔗 https://hardverapro.hu/termek/123",
        webhook_type="discord",
        username="PYHABOT",
        avatar_url="https://via.placeholder.com/150/00ff00/000000?text=PYHABOT",
        verbose=True
    )


async def test_slack_webhook():
    """Test Slack webhook with sample data."""
    webhook_url = input("Enter Slack webhook URL: ").strip()
    if not webhook_url:
        print("No webhook URL provided")
        return False
    
    return await test_webhook(
        webhook_url,
        "🆕 Új hirdetés: Eladó használt laptop\n💰 Ár: 150 000 Ft\n📍 Helyszín: Budapest\n👤 Eladó: János\n🔗 https://hardverapro.hu/termek/123",
        webhook_type="slack",
        username="PYHABOT",
        verbose=True
    )


async def test_generic_webhook():
    """Test generic webhook with sample data."""
    webhook_url = input("Enter generic webhook URL: ").strip()
    if not webhook_url:
        print("No webhook URL provided")
        return False
    
    return await test_webhook(
        webhook_url,
        "New advertisement: Eladó használt laptop\nPrice: 150 000 HUF\nLocation: Budapest\nSeller: János\nURL: https://hardverapro.hu/termek/123",
        webhook_type="generic",
        verbose=True
    )


async def interactive_test():
    """Interactive webhook testing."""
    print("🔧 PYHABOT Webhook Testing Tool")
    print("=" * 40)
    
    while True:
        print("\nChoose webhook type to test:")
        print("1. Discord webhook")
        print("2. Slack webhook")
        print("3. Generic webhook")
        print("4. Custom webhook URL")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            await test_discord_webhook()
        elif choice == "2":
            await test_slack_webhook()
        elif choice == "3":
            await test_generic_webhook()
        elif choice == "4":
            webhook_url = input("Enter webhook URL: ").strip()
            if not webhook_url:
                print("No webhook URL provided")
                continue
            
            message = input("Enter test message (or press Enter for default): ").strip()
            if not message:
                message = "Test message from PYHABOT webhook testing tool"
            
            webhook_type = input("Enter webhook type (discord/slack/generic) [default: generic]: ").strip()
            if not webhook_type:
                webhook_type = "generic"
            
            username = input("Enter username (optional): ").strip() or None
            avatar_url = input("Enter avatar URL (optional): ").strip() or None
            
            await test_webhook(
                webhook_url,
                message,
                webhook_type,
                username,
                avatar_url,
                verbose=True
            )
        elif choice == "5":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid choice. Please try again.")
        
        print("\n" + "=" * 40)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test PYHABOT webhooks")
    parser.add_argument("--url", help="Webhook URL to test")
    parser.add_argument("--message", default="Test message from PYHABOT", help="Message to send")
    parser.add_argument("--type", choices=["discord", "slack", "generic"], default="generic", help="Webhook type")
    parser.add_argument("--username", help="Webhook username")
    parser.add_argument("--avatar", help="Webhook avatar URL")
    parser.add_argument("--retries", type=int, default=3, help="Maximum retries")
    parser.add_argument("--delay", type=float, default=1.0, help="Base delay between retries")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--interactive", action="store_true", help="Interactive testing mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        asyncio.run(interactive_test())
    elif args.url:
        asyncio.run(test_webhook(
            args.url,
            args.message,
            args.type,
            args.username,
            args.avatar,
            args.retries,
            args.delay,
            args.verbose
        ))
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python test_webhook_manual.py --url https://discord.com/api/webhooks/123/abc --type discord")
        print("  python test_webhook_manual.py --interactive")


if __name__ == "__main__":
    main()