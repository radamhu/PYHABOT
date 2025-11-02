"""
Tests for webhook API endpoints.

This module tests the webhook functionality including
configuration, testing, and notification sending.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from aiohttp import ClientSession

from src.pyhabot.api.main import app
from src.pyhabot.api.models import (
    WebhookTestRequest,
    WebhookTestResponse,
    SetWebhookRequest
)
from src.pyhabot.adapters.notifications.webhook import WebhookNotifier


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_webhook_notifier():
    """Create mock webhook notifier."""
    notifier = Mock(spec=WebhookNotifier)
    notifier.send_webhook_notification = AsyncMock(return_value=True)
    notifier.session = Mock(spec=ClientSession)
    return notifier


@pytest.fixture
def sample_webhook_request():
    """Sample webhook test request."""
    return WebhookTestRequest(
        webhook_url="https://discord.com/api/webhooks/123/abc",
        webhook_type="discord",
        webhook_username="PYHABOT",
        test_message="Test notification from PYHABOT"
    )


@pytest.fixture
def sample_set_webhook_request():
    """Sample set webhook request."""
    return SetWebhookRequest(
        webhook_url="https://discord.com/api/webhooks/123/abc",
        webhook_type="discord",
        webhook_username="PYHABOT"
    )


class TestWebhookAPI:
    """Test webhook API endpoints."""
    
    @patch('src.pyhabot.api.dependencies.get_notification_service')
    @patch('src.pyhabot.adapters.api.webhook_api._perform_webhook_test')
    def test_test_webhook_success(
        self, 
        mock_perform_test, 
        mock_get_notification_service,
        client,
        sample_webhook_request
    ):
        """Test successful webhook test."""
        # Setup mocks
        mock_perform_test.return_value = WebhookTestResponse(
            success=True,
            response_status=200,
            response_body="OK",
            error_message=None,
            attempts=1,
            total_time=0.123
        )
        
        # Make request
        response = client.post(
            "/api/v1/webhooks/test",
            json=sample_webhook_request.dict()
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["response_status"] == 200
        assert data["attempts"] == 1
        assert data["total_time"] == 0.123
    
    def test_test_webhook_invalid_url(self, client):
        """Test webhook test with invalid URL."""
        invalid_request = {
            "webhook_url": "invalid-url",
            "webhook_type": "discord"
        }
        
        response = client.post(
            "/api/v1/webhooks/test",
            json=invalid_request
        )
        
        assert response.status_code == 422
    
    def test_test_webhook_invalid_type(self, client):
        """Test webhook test with invalid webhook type."""
        invalid_request = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "webhook_type": "invalid_type"
        }
        
        response = client.post(
            "/api/v1/webhooks/test",
            json=invalid_request
        )
        
        assert response.status_code == 422
    
    @patch('src.pyhabot.api.dependencies.get_watch_service')
    def test_get_webhook_config_success(
        self, 
        mock_get_watch_service,
        client
    ):
        """Test getting webhook configuration."""
        # Setup mock
        mock_watch_service = Mock()
        mock_watch = Mock()
        mock_watch.id = 1
        mock_watch.webhook = "https://discord.com/api/webhooks/123/abc"
        mock_watch_service.get_watch.return_value = mock_watch
        mock_get_watch_service.return_value = mock_watch_service
        
        # Make request
        response = client.get("/api/v1/webhooks/watches/1/config")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["watch_id"] == 1
        assert data["webhook_url"] == "https://discord.com/api/webhooks/123/abc"
        assert data["webhook_type"] == "generic"  # Default value
    
    @patch('src.pyhabot.api.dependencies.get_watch_service')
    def test_get_webhook_config_not_found(
        self, 
        mock_get_watch_service,
        client
    ):
        """Test getting webhook configuration for non-existent watch."""
        # Setup mock
        mock_watch_service = Mock()
        mock_watch_service.get_watch.return_value = None
        mock_get_watch_service.return_value = mock_watch_service
        
        # Make request
        response = client.get("/api/v1/webhooks/watches/999/config")
        
        # Assertions
        assert response.status_code == 404
    
    @patch('src.pyhabot.api.dependencies.get_watch_service')
    @patch('src.pyhabot.api.dependencies.get_notification_service')
    def test_test_watch_webhook_success(
        self, 
        mock_get_notification_service,
        mock_get_watch_service,
        client
    ):
        """Test testing webhook for a specific watch."""
        # Setup mocks
        mock_watch_service = Mock()
        mock_watch = Mock()
        mock_watch.id = 1
        mock_watch.webhook = "https://discord.com/api/webhooks/123/abc"
        mock_watch_service.get_watch.return_value = mock_watch
        mock_get_watch_service.return_value = mock_watch_service
        
        mock_notification_service = Mock()
        mock_webhook_notifier = Mock()
        mock_webhook_notifier.send_webhook_notification = AsyncMock(return_value=True)
        mock_notification_service.webhook_notifier = mock_webhook_notifier
        mock_get_notification_service.return_value = mock_notification_service
        
        # Make request
        response = client.post(
            "/api/v1/webhooks/watches/1/test",
            params={"test_message": "Custom test message"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["attempts"] == 1
    
    @patch('src.pyhabot.api.dependencies.get_watch_service')
    def test_test_watch_webhook_no_webhook(
        self, 
        mock_get_watch_service,
        client
    ):
        """Test testing webhook for watch with no webhook configured."""
        # Setup mock
        mock_watch_service = Mock()
        mock_watch = Mock()
        mock_watch.id = 1
        mock_watch.webhook = None
        mock_watch_service.get_watch.return_value = mock_watch
        mock_get_watch_service.return_value = mock_watch_service
        
        # Make request
        response = client.post("/api/v1/webhooks/watches/1/test")
        
        # Assertions
        assert response.status_code == 400
        assert "No webhook configured" in response.json()["detail"]
    
    def test_get_webhook_types(self, client):
        """Test getting supported webhook types."""
        response = client.get("/api/v1/webhooks/types")
        
        assert response.status_code == 200
        data = response.json()
        assert "webhook_types" in data
        assert "discord" in data["webhook_types"]
        assert "slack" in data["webhook_types"]
        assert "generic" in data["webhook_types"]
        
        # Check Discord webhook type details
        discord_config = data["webhook_types"]["discord"]
        assert discord_config["name"] == "Discord"
        assert "embeds" in discord_config["features"]
        assert discord_config["payload_format"] == "discord_webhook"
        
        # Check retry policy
        assert "retry_policy" in data
        retry_policy = data["retry_policy"]
        assert retry_policy["max_retries"] == 3
        assert retry_policy["backoff_factor"] == 2.0


class TestWebhookNotifierIntegration:
    """Test webhook notifier integration."""
    
    @pytest.mark.asyncio
    async def test_discord_webhook_payload(self):
        """Test Discord webhook payload preparation."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(session)
            
            payload = notifier._prepare_discord_payload(
                "Test message",
                username="PYHABOT",
                embeds=[{"title": "Test Embed"}]
            )
            
            assert payload["content"] == "Test message"
            assert payload["username"] == "PYHABOT"
            assert payload["embeds"] == [{"title": "Test Embed"}]
            assert "avatar_url" not in payload  # Should be filtered out
    
    @pytest.mark.asyncio
    async def test_slack_webhook_payload(self):
        """Test Slack webhook payload preparation."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(session)
            
            payload = notifier._prepare_slack_payload(
                "Test message",
                username="PYHABOT",
                attachments=[{"text": "Test Attachment"}]
            )
            
            assert payload["text"] == "Test message"
            assert payload["username"] == "PYHABOT"
            assert payload["attachments"] == [{"text": "Test Attachment"}]
            assert "icon_url" not in payload  # Should be filtered out
    
    @pytest.mark.asyncio
    async def test_generic_webhook_payload(self):
        """Test generic webhook payload preparation."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(session)
            
            payload = notifier._prepare_generic_payload(
                "Test message",
                custom_field="custom_value"
            )
            
            assert payload["message"] == "Test message"
            assert payload["source"] == "PYHABOT"
            assert payload["custom_field"] == "custom_value"
            assert "timestamp" in payload
    
    @pytest.mark.asyncio
    async def test_delay_calculation(self):
        """Test exponential backoff delay calculation."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(
                session,
                base_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                jitter=False
            )
            
            # Test exponential backoff
            delay_0 = notifier._calculate_delay(0)
            delay_1 = notifier._calculate_delay(1)
            delay_2 = notifier._calculate_delay(2)
            
            assert delay_0 == 1.0
            assert delay_1 == 2.0
            assert delay_2 == 4.0
            
            # Test max delay limit
            delay_high = notifier._calculate_delay(10)
            assert delay_high == 10.0
    
    @pytest.mark.asyncio
    async def test_delay_calculation_with_jitter(self):
        """Test delay calculation with jitter."""
        async with ClientSession() as session:
            notifier = WebhookNotifier(
                session,
                base_delay=1.0,
                backoff_factor=2.0,
                jitter=True
            )
            
            delay = notifier._calculate_delay(1)
            # With jitter, delay should be between 1.5 and 2.5 (2.0 ± 25%)
            assert 1.5 <= delay <= 2.5


if __name__ == "__main__":
    pytest.main([__file__])