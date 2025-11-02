"""
Integration tests for webhook functionality.

This module tests webhook functionality end-to-end including
notification sending, retry logic, and error handling.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from aiohttp import web, ClientSession, ClientTimeout
from aiohttp.test_utils import TestServer, TestClient

from src.pyhabot.adapters.notifications.webhook import WebhookNotifier
from src.pyhabot.domain.services import NotificationService
from src.pyhabot.domain.models import Watch, Advertisement, NotificationTarget, NotificationType


@pytest.fixture
async def webhook_server():
    """Create a test webhook server."""
    app = web.Application()
    
    # Store received webhooks for testing
    received_webhooks = []
    
    async def handle_discord_webhook(request):
        data = await request.json()
        received_webhooks.append({
            "type": "discord",
            "data": data,
            "headers": dict(request.headers)
        })
        return web.Response(status=204)
    
    async def handle_slack_webhook(request):
        data = await request.json()
        received_webhooks.append({
            "type": "slack", 
            "data": data,
            "headers": dict(request.headers)
        })
        return web.Response(status=200, text="ok")
    
    async def handle_generic_webhook(request):
        data = await request.json()
        received_webhooks.append({
            "type": "generic",
            "data": data,
            "headers": dict(request.headers)
        })
        return web.Response(status=200, json={"status": "received"})
    
    async def handle_error_webhook(request):
        return web.Response(status=500, text="Internal Server Error")
    
    async def handle_rate_limit_webhook(request):
        return web.Response(
            status=429, 
            text="Rate Limited",
            headers={"Retry-After": "60"}
        )
    
    app.router.add_post("/discord", handle_discord_webhook)
    app.router.add_post("/slack", handle_slack_webhook)
    app.router.add_post("/generic", handle_generic_webhook)
    app.router.add_post("/error", handle_error_webhook)
    app.router.add_post("/rate-limit", handle_rate_limit_webhook)
    
    server = TestServer(app)
    await server.start_server()
    
    # Store reference for tests
    server.received_webhooks = received_webhooks
    
    yield server
    
    await server.close()


class TestWebhookIntegration:
    """Test webhook integration end-to-end."""
    
    @pytest.mark.asyncio
    async def test_discord_webhook_success(self, webhook_server):
        """Test successful Discord webhook notification."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(session)
            
            webhook_url = f"{webhook_server.make_url('/discord')}"
            
            success = await notifier.send_webhook_notification(
                webhook_url,
                "Test Discord message",
                webhook_type="discord",
                username="PYHABOT",
                embeds=[{
                    "title": "New Advertisement",
                    "description": "Test description",
                    "color": 0x00ff00
                }]
            )
            
            assert success is True
            assert len(webhook_server.received_webhooks) == 1
            
            webhook_data = webhook_server.received_webhooks[0]
            assert webhook_data["type"] == "discord"
            assert webhook_data["data"]["content"] == "Test Discord message"
            assert webhook_data["data"]["username"] == "PYHABOT"
            assert len(webhook_data["data"]["embeds"]) == 1
            assert webhook_data["data"]["embeds"][0]["title"] == "New Advertisement"
    
    @pytest.mark.asyncio
    async def test_slack_webhook_success(self, webhook_server):
        """Test successful Slack webhook notification."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(session)
            
            webhook_url = f"{webhook_server.make_url('/slack')}"
            
            success = await notifier.send_webhook_notification(
                webhook_url,
                "Test Slack message",
                webhook_type="slack",
                username="PYHABOT",
                attachments=[{
                    "color": "good",
                    "text": "Test attachment"
                }]
            )
            
            assert success is True
            assert len(webhook_server.received_webhooks) == 1
            
            webhook_data = webhook_server.received_webhooks[0]
            assert webhook_data["type"] == "slack"
            assert webhook_data["data"]["text"] == "Test Slack message"
            assert webhook_data["data"]["username"] == "PYHABOT"
            assert len(webhook_data["data"]["attachments"]) == 1
    
    @pytest.mark.asyncio
    async def test_generic_webhook_success(self, webhook_server):
        """Test successful generic webhook notification."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(session)
            
            webhook_url = f"{webhook_server.make_url('/generic')}"
            
            success = await notifier.send_webhook_notification(
                webhook_url,
                "Test generic message",
                webhook_type="generic",
                custom_field="custom_value"
            )
            
            assert success is True
            assert len(webhook_server.received_webhooks) == 1
            
            webhook_data = webhook_server.received_webhooks[0]
            assert webhook_data["type"] == "generic"
            assert webhook_data["data"]["message"] == "Test generic message"
            assert webhook_data["data"]["source"] == "PYHABOT"
            assert webhook_data["data"]["custom_field"] == "custom_value"
            assert "timestamp" in webhook_data["data"]
    
    @pytest.mark.asyncio
    async def test_webhook_server_error_retry(self, webhook_server):
        """Test webhook retry on server error."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(
                session,
                max_retries=2,
                base_delay=0.1,  # Short delay for testing
                jitter=False
            )
            
            webhook_url = f"{webhook_server.make_url('/error')}"
            
            success = await notifier.send_webhook_notification(
                webhook_url,
                "Test message",
                webhook_type="generic"
            )
            
            assert success is False
            # Should have attempted 3 times (1 initial + 2 retries)
            # We can't easily track this without more complex mocking
    
    @pytest.mark.asyncio
    async def test_webhook_rate_limit_handling(self, webhook_server):
        """Test webhook rate limit handling."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(
                session,
                max_retries=1,
                base_delay=0.1,
                jitter=False
            )
            
            webhook_url = f"{webhook_server.make_url('/rate-limit')}"
            
            success = await notifier.send_webhook_notification(
                webhook_url,
                "Test message",
                webhook_type="generic"
            )
            
            assert success is False
    
    @pytest.mark.asyncio
    async def test_notification_service_with_webhook(self, webhook_server):
        """Test NotificationService with webhook integration."""
        # Create mock watch and advertisement
        watch = Watch.create_new(1, "https://example.com/search")
        watch.webhook = f"{webhook_server.make_url('/discord')}"
        
        ad = Advertisement.create_new({
            "id": 123,
            "title": "Test Advertisement",
            "url": "https://example.com/ad/123",
            "price": 100000,
            "city": "Budapest",
            "date": "2025-11-02",
            "pinned": False,
            "seller_name": "Test Seller",
            "seller_url": "https://example.com/seller/1",
            "seller_rates": "100% (10)",
            "image": "https://example.com/image.jpg"
        }, watch_id=1)
        
        async with ClientSession() as session:
            webhook_notifier = WebhookNotifier(session)
            notification_service = NotificationService(
                notifier=webhook_notifier,  # Use webhook as main notifier
                webhook_notifier=webhook_notifier
            )
            
            # Send new ad notification
            results = await notification_service.send_new_ad_notifications(watch, [ad])
            
            assert len(results) == 1
            assert results[0] is True
            assert len(webhook_server.received_webhooks) == 1
            
            webhook_data = webhook_server.received_webhooks[0]
            assert webhook_data["type"] == "discord"
            assert "Új hirdetés" in webhook_data["data"]["content"]
            assert ad.title in webhook_data["data"]["content"]
    
    @pytest.mark.asyncio
    async def test_price_change_notification(self, webhook_server):
        """Test price change notification via webhook."""
        # Create mock watch and advertisement with price change
        watch = Watch.create_new(1, "https://example.com/search")
        watch.webhook = f"{webhook_server.make_url('/slack')}"
        
        ad = Advertisement.create_new({
            "id": 123,
            "title": "Test Advertisement",
            "url": "https://example.com/ad/123",
            "price": 90000,  # New price after change
            "city": "Budapest",
            "date": "2025-11-02",
            "pinned": False,
            "seller_name": "Test Seller",
            "seller_url": "https://example.com/seller/1",
            "seller_rates": "100% (10)",
            "image": "https://example.com/image.jpg"
        }, watch_id=1)
        
        # Simulate price change
        ad.prev_prices = [100000]  # Previous price
        ad.price_alert = True
        
        async with ClientSession() as session:
            webhook_notifier = WebhookNotifier(session)
            notification_service = NotificationService(
                notifier=webhook_notifier,
                webhook_notifier=webhook_notifier
            )
            
            # Send price change notification
            results = await notification_service.send_price_change_notifications(watch, [ad])
            
            assert len(results) == 1
            assert results[0] is True
            assert len(webhook_server.received_webhooks) == 1
            
            webhook_data = webhook_server.received_webhooks[0]
            assert webhook_data["type"] == "slack"
            assert "Árváltozás" in webhook_data["data"]["text"]
            assert ad.title in webhook_data["data"]["text"]
    
    @pytest.mark.asyncio
    async def test_webhook_custom_headers(self, webhook_server):
        """Test webhook with custom headers."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(session)
            
            webhook_url = f"{webhook_server.make_url('/generic')}"
            
            success = await notifier.send_webhook_notification(
                webhook_url,
                "Test message with headers",
                webhook_type="generic",
                headers={
                    "Authorization": "Bearer token123",
                    "X-Custom-Header": "custom-value"
                }
            )
            
            assert success is True
            assert len(webhook_server.received_webhooks) == 1
            
            webhook_data = webhook_server.received_webhooks[0]
            headers = webhook_data["headers"]
            assert headers["Authorization"] == "Bearer token123"
            assert headers["X-Custom-Header"] == "custom-value"
            assert headers["Content-Type"] == "application/json"


if __name__ == "__main__":
    pytest.main([__file__])