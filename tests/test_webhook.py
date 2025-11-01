#!/usr/bin/env python3
"""
Discord Webhook Test Script for PYHABOT.

This script tests the Discord webhook sending functionality
by sending test messages to a specified webhook URL.
"""

import asyncio
import argparse
import json
import sys
from typing import Dict, Any, Optional

# Add the src directory to the path so we can import pyhabot modules
sys.path.insert(0, 'src')

from pyhabot.adapters.notifications.webhook import WebhookNotifier
from pyhabot.logging import get_logger
import aiohttp

logger = get_logger(__name__)


async def test_discord_webhook(
    webhook_url: str, 
    session: aiohttp.ClientSession,
    test_type: str = "basic"
) -> bool:
    """Test Discord webhook with different message types."""
    
    notifier = WebhookNotifier(session)
    
    test_cases = {
        "basic": {
            "message": "🧪 PYHABOT Webhook Test - Basic Message",
            "webhook_type": "discord",
            "username": "PYHABOT Test"
        },
        "new_ad": {
            "message": "🆕 Test New Ad Notification\n💰 Ár: 15 000 Ft\n📍 Helyszín: Budapest\n👤 Eladó: Test User\n🔗 https://hardverapro.hu/123456",
            "webhook_type": "discord",
            "username": "PYHABOT",
            "embeds": [{
                "title": "Új hirdetés: Test Product",
                "description": "Ez egy teszt hirdetés leírása",
                "color": 0x00ff00,
                "fields": [
                    {"name": "Ár", "value": "15 000 Ft", "inline": True},
                    {"name": "Helyszín", "value": "Budapest", "inline": True}
                ]
            }]
        },
        "price_change": {
            "message": "💸 Árváltozás: Test Product\n📉 Régi ár: 20 000 Ft\n📈 Új ár: 15 000 Ft\n📍 Helyszín: Debrecen",
            "webhook_type": "discord",
            "username": "PYHABOT Price Alert",
            "embeds": [{
                "title": "Árváltozás értesítő",
                "description": "A termék ára megváltozott!",
                "color": 0xff9900,
                "fields": [
                    {"name": "Régi ár", "value": "20 000 Ft", "inline": True},
                    {"name": "Új ár", "value": "15 000 Ft", "inline": True},
                    {"name": "Különbség", "value": "-5 000 Ft (-25%)", "inline": True}
                ]
            }]
        },
        "error": {
            "message": "❌ PYHABOT Test Error Message\nThis is a test error notification",
            "webhook_type": "discord",
            "username": "PYHABOT Error",
            "embeds": [{
                "title": "Hiba történt",
                "description": "Ez egy teszt hibaüzenet",
                "color": 0xff0000
            }]
        }
    }
    
    if test_type not in test_cases:
        print(f"❌ Unknown test type: {test_type}")
        print(f"Available types: {', '.join(test_cases.keys())}")
        return False
    
    test_data = test_cases[test_type]
    
    print(f"🧪 Testing Discord webhook ({test_type})...")
    print(f"📡 URL: {webhook_url}")
    print(f"📝 Message: {test_data['message'][:50]}...")
    
    try:
        success = await notifier.send_webhook_notification(
            webhook_url,
            test_data["message"],
            **{k: v for k, v in test_data.items() if k != 'message'}
        )
        
        if success:
            print(f"✅ Webhook test ({test_type}) successful!")
            return True
        else:
            print(f"❌ Webhook test ({test_type}) failed!")
            return False
            
    except Exception as e:
        print(f"❌ Webhook test ({test_type}) error: {e}")
        logger.error(f"Webhook test error: {e}")
        return False


async def test_webhook_connectivity(webhook_url: str) -> bool:
    """Test basic connectivity to the webhook URL."""
    print(f"🔍 Testing webhook connectivity...")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Send a simple ping-like request
            payload = {
                "content": "🔔 PYHABOT Connectivity Test",
                "username": "PYHABOT Test"
            }
            
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    print("✅ Webhook endpoint reachable (204 No Content)")
                    return True
                elif 200 <= response.status < 300:
                    print(f"✅ Webhook endpoint reachable ({response.status})")
                    return True
                else:
                    print(f"❌ Webhook returned error status: {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    return False
                    
    except asyncio.TimeoutError:
        print("❌ Webhook request timed out")
        return False
    except aiohttp.ClientError as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test PYHABOT Discord webhook functionality"
    )
    parser.add_argument(
        "webhook_url",
        help="Discord webhook URL to test"
    )
    parser.add_argument(
        "--test-type",
        choices=["basic", "new_ad", "price_change", "error", "all"],
        default="basic",
        help="Type of test to run (default: basic)"
    )
    parser.add_argument(
        "--connectivity",
        action="store_true",
        help="Test basic connectivity first"
    )
    
    args = parser.parse_args()
    
    if not args.webhook_url:
        print("❌ Webhook URL is required")
        return 1
    
    print("🚀 PYHABOT Discord Webhook Test")
    print("=" * 50)
    
    # Test connectivity first if requested
    if args.connectivity:
        if not await test_webhook_connectivity(args.webhook_url):
            print("❌ Connectivity test failed, aborting further tests")
            return 1
        print()
    
    # Run webhook tests
    async with aiohttp.ClientSession() as session:
        if args.test_type == "all":
            test_types = ["basic", "new_ad", "price_change", "error"]
            results = []
            
            for test_type in test_types:
                result = await test_discord_webhook(args.webhook_url, session, test_type)
                results.append(result)
                print()
                
            success_count = sum(results)
            total_count = len(results)
            
            print("=" * 50)
            print(f"📊 Test Results: {success_count}/{total_count} passed")
            
            if success_count == total_count:
                print("🎉 All tests passed!")
                return 0
            else:
                print("❌ Some tests failed")
                return 1
        else:
            success = await test_discord_webhook(args.webhook_url, session, args.test_type)
            return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))