"""
Webhook notification adapter for PYHABOT.

This adapter provides webhook notification capabilities with retry logic,
backoff strategies, and proper error handling for non-2xx responses.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import aiohttp

from ...domain.ports import NotifierPort

logger = logging.getLogger(__name__)


class WebhookNotifier(NotifierPort):
    """Webhook notification adapter with retry and backoff."""
    
    def __init__(
        self,
        session: aiohttp.ClientSession,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.session = session
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    async def send_notification(
        self, 
        target,  # Not used for webhooks
        message: str, 
        no_preview: bool = False,
        **kwargs
    ) -> bool:
        """
        Send a notification to a target (not implemented for webhooks).
        
        Webhooks use send_webhook_notification instead.
        """
        logger.warning("send_notification not supported for webhooks. Use send_webhook_notification.")
        return False
    
    async def send_webhook_notification(
        self, 
        webhook_url: str, 
        message: str, 
        **kwargs
    ) -> bool:
        """
        Send a notification via webhook with retry logic.
        
        Args:
            webhook_url: The webhook URL
            message: The message to send
            **kwargs: Additional webhook-specific options
            
        Returns:
            True if successful, False otherwise
        """
        payload = self._prepare_payload(message, **kwargs)
        
        for attempt in range(self.max_retries + 1):
            try:
                success = await self._send_webhook_request(webhook_url, payload, attempt)
                if success:
                    logger.info(f"Webhook notification sent successfully to {webhook_url}")
                    return True
                    
            except Exception as e:
                logger.warning(f"Webhook attempt {attempt + 1} failed for {webhook_url}: {e}")
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"Retrying webhook in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All webhook attempts failed for {webhook_url}")
        
        return False
    
    def _prepare_payload(self, message: str, **kwargs) -> Dict[str, Any]:
        """Prepare webhook payload based on webhook type."""
        # Default to Discord webhook format
        webhook_type = kwargs.get("webhook_type", "discord")
        
        if webhook_type == "discord":
            return self._prepare_discord_payload(message, **kwargs)
        elif webhook_type == "slack":
            return self._prepare_slack_payload(message, **kwargs)
        elif webhook_type == "generic":
            return self._prepare_generic_payload(message, **kwargs)
        else:
            logger.warning(f"Unknown webhook type: {webhook_type}, using generic")
            return self._prepare_generic_payload(message, **kwargs)
    
    def _prepare_discord_payload(self, message: str, **kwargs) -> Dict[str, Any]:
        """Prepare Discord webhook payload."""
        payload = {
            "content": message,
            "username": kwargs.get("username", "PYHABOT"),
            "avatar_url": kwargs.get("avatar_url"),
            "tts": kwargs.get("tts", False)
        }
        
        # Add embeds if provided
        if "embeds" in kwargs:
            payload["embeds"] = kwargs["embeds"]
        
        # Remove None values
        return {k: v for k, v in payload.items() if v is not None}
    
    def _prepare_slack_payload(self, message: str, **kwargs) -> Dict[str, Any]:
        """Prepare Slack webhook payload."""
        payload = {
            "text": message,
            "username": kwargs.get("username", "PYHABOT"),
            "icon_url": kwargs.get("avatar_url")
        }
        
        # Add attachments if provided
        if "attachments" in kwargs:
            payload["attachments"] = kwargs["attachments"]
        
        # Remove None values
        return {k: v for k, v in payload.items() if v is not None}
    
    def _prepare_generic_payload(self, message: str, **kwargs) -> Dict[str, Any]:
        """Prepare generic webhook payload."""
        payload = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "PYHABOT"
        }
        
        # Add any additional fields
        payload.update({k: v for k, v in kwargs.items() if k not in ["webhook_type"]})
        
        return payload
    
    async def _send_webhook_request(
        self, 
        webhook_url: str, 
        payload: Dict[str, Any], 
        attempt: int
    ) -> bool:
        """Send webhook request and handle response."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"PYHABOT-Webhook/1.0 (Attempt {attempt + 1})"
        }
        
        # Add custom headers if provided
        if "headers" in payload:
            headers.update(payload.pop("headers"))
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        try:
            async with self.session.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=timeout
            ) as response:
                if response.status == 204:
                    # No content - success
                    return True
                elif 200 <= response.status < 300:
                    # Success with content
                    try:
                        await response.json()  # Consume response body
                    except:
                        await response.text()  # Fallback to text
                    return True
                elif response.status == 429:
                    # Rate limited - extract retry-after if available
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        logger.warning(f"Rate limited by webhook, retry-after: {retry_after}")
                        # This will be handled by the retry logic
                    return False
                elif 400 <= response.status < 500:
                    # Client error - don't retry
                    error_text = await response.text()
                    logger.error(f"Webhook client error {response.status}: {error_text}")
                    return False
                else:
                    # Server error - will retry
                    error_text = await response.text()
                    logger.warning(f"Webhook server error {response.status}: {error_text}")
                    return False
                    
        except asyncio.TimeoutError:
            logger.warning(f"Webhook request timed out (attempt {attempt + 1})")
            return False
        except aiohttp.ClientError as e:
            logger.warning(f"Webhook network error (attempt {attempt + 1}): {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected webhook error (attempt {attempt + 1}): {e}")
            return False
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter (±25% of delay)
            import random
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def format_message(self, message_type: str, **kwargs) -> str:
        """
        Format a message according to the message type.
        
        For webhooks, we use the base formatting since the webhook
        payload preparation handles platform-specific formatting.
        """
        templates = {
            "new_ad": (
                "🆕 Új hirdetés: {title}\n"
                "💰 Ár: {price} Ft\n"
                "📍 Helyszín: {city}\n"
                "👤 Eladó: {seller_name}\n"
                "🔗 {url}"
            ),
            "price_change": (
                "💸 Árváltozás: {title}\n"
                "📉 Régi ár: {old_price} Ft\n"
                "📈 Új ár: {new_price} Ft\n"
                "📍 Helyszín: {city}\n"
                "🔗 {url}"
            ),
            "error": "❌ Hiba történt: {error}",
            "info": "ℹ️ {message}",
            "success": "✅ {message}"
        }
        
        template = templates.get(message_type, "{message}")
        
        # Format price values
        if "price" in kwargs and kwargs["price"] is not None:
            kwargs["price"] = f"{kwargs['price']:,}".replace(",", " ")
        if "old_price" in kwargs and kwargs["old_price"] is not None:
            kwargs["old_price"] = f"{kwargs['old_price']:,}".replace(",", " ")
        if "new_price" in kwargs and kwargs["new_price"] is not None:
            kwargs["new_price"] = f"{kwargs['new_price']:,}".replace(",", " ")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing template variable {e} for message type {message_type}")
            return f"Message formatting error: {e}"


class WebhookError(Exception):
    """Raised when webhook operations fail after all retries."""
    pass


class RateLimitError(WebhookError):
    """Raised when webhook is rate limited."""
    pass