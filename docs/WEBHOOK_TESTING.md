# PYHABOT Discord Webhook Testing Guide

This guide provides comprehensive instructions for testing Discord webhook functionality in PYHABOT, both in console and Docker environments.

## Overview

PYHABOT supports sending notifications to Discord webhooks for:
- New advertisements
- Price changes
- Error notifications
- Custom messages

The webhook functionality is implemented in `src/pyhabot/adapters/notifications/webhook.py` and supports Discord-specific formatting with embeds.

## Testing Options

### 1. Console Testing

#### Standalone Test Script

The `test_webhook.py` script provides comprehensive webhook testing:

```bash
# Basic test
python test_webhook.py "https://your-discord-webhook-url" --test-type basic

# Test with connectivity check
python test_webhook.py "https://your-discord-webhook-url" --test-type basic --connectivity

# Test all message types
python test_webhook.py "https://your-discord-webhook-url" --test-type all

# Test specific message types
python test_webhook.py "https://your-discord-webhook-url" --test-type new_ad
python test_webhook.py "https://your-discord-webhook-url" --test-type price_change
python test_webhook.py "https://your-discord-webhook-url" --test-type error
```

#### CLI Integration Test

Use the built-in CLI command:

```bash
# Test webhook through CLI
python -m pyhabot.simple_cli test-webhook "https://your-discord-webhook-url" --test-type basic

# Test all message types
python -m pyhabot.simple_cli test-webhook "https://your-discord-webhook-url" --test-type all
```

### 2. Docker Testing

#### Docker Test Script

The `test_webhook_docker.sh` script provides automated Docker testing:

```bash
# Set up test environment
./test_webhook_docker.sh --setup

# Test against local webhook server
./test_webhook_docker.sh --test-local

# Test against Discord webhook
./test_webhook_docker.sh --test-discord "https://your-discord-webhook-url"

# Test CLI command in Docker
./test_webhook_docker.sh --test-cli

# Test CLI with specific URL
./test_webhook_docker.sh --test-cli "https://your-discord-webhook-url"

# Show container logs
./test_webhook_docker.sh --logs

# Clean up test environment
./test_webhook_docker.sh --cleanup
```

#### Manual Docker Testing

```bash
# Build and run container
docker compose -f docker-compose.test.yml up -d pyhabot-webhook-test

# Execute tests in container
docker exec -it pyhabot-webhook-test python test_webhook.py "https://your-discord-webhook-url" --test-type all

# Test CLI in container
docker exec -it pyhabot-webhook-test python -m pyhabot.simple_cli test-webhook "https://your-discord-webhook-url"

# Clean up
docker compose -f docker-compose.test.yml down
```

## Test Webhook Services

### For Testing Without Real Discord Webhook

1. **httpbin.org** - Echoes back requests
   ```bash
   python test_webhook.py "https://httpbin.org/post" --test-type all
   ```

2. **webhook.site** - Provides temporary webhook URLs
   - Visit https://webhook.site to get a temporary URL
   - Use the provided URL for testing

3. **Local Test Server** (Docker only)
   ```bash
   ./test_webhook_docker.sh --test-local
   ```

## Message Types

### Basic Message
Simple text notification:
```
🧪 PYHABOT Webhook Test - Basic Message
```

### New Advertisement
Formatted new ad notification with embed:
```
🆕 Test New Ad Notification
💰 Ár: 15 000 Ft
📍 Helyszín: Budapest
👤 Eladó: Test User
🔗 https://hardverapro.hu/123456
```

### Price Change
Price change notification with embed:
```
💸 Árváltozás: Test Product
📉 Régi ár: 20 000 Ft
📈 Új ár: 15 000 Ft
📍 Helyszín: Debrecen
```

### Error Message
Error notification with embed:
```
❌ PYHABOT Test Error Message
This is a test error notification
```

## Discord Webhook Setup

1. **Create Discord Webhook**
   - Open your Discord server settings
   - Go to "Integrations" → "Webhooks"
   - Click "New Webhook"
   - Give it a name (e.g., "PYHABOT")
   - Select the channel
   - Copy the webhook URL

2. **Configure PYHABOT**
   ```bash
   # Set webhook for a watch
   python -m pyhabot.simple_cli set-webhook <watch_id> "https://your-discord-webhook-url"
   
   # Test the webhook
   python -m pyhabot.simple_cli test-webhook "https://your-discord-webhook-url"
   ```

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check network connectivity
   - Verify webhook URL is correct
   - Check firewall settings

2. **401 Unauthorized**
   - Verify Discord webhook URL is valid
   - Check if webhook was deleted or disabled

3. **429 Rate Limited**
   - Discord webhooks have rate limits
   - Wait and retry automatically handled by the code

4. **Container Network Issues**
   - Ensure Docker containers can reach external URLs
   - Check DNS resolution in containers

### Debugging

1. **Enable Debug Logging**
   ```bash
   export LOG_LEVEL=DEBUG
   python test_webhook.py "https://your-discord-webhook-url" --test-type basic
   ```

2. **Check Container Logs**
   ```bash
   ./test_webhook_docker.sh --logs
   # or
   docker logs pyhabot-webhook-test
   ```

3. **Test Connectivity First**
   ```bash
   python test_webhook.py "https://your-discord-webhook-url" --connectivity
   ```

## Integration with PYHABOT

Once webhook testing is successful, integrate with PYHABOT:

1. **Add a Watch**
   ```bash
   python -m pyhabot.simple_cli add-watch "https://hardverapro.hu/your-search-url"
   ```

2. **Set Webhook**
   ```bash
   python -m pyhabot.simple_cli set-webhook 1 "https://your-discord-webhook-url"
   ```

3. **Run PYHABOT**
   ```bash
   python -m pyhabot.simple_cli run
   ```

4. **Force Test Scrape**
   ```bash
   python -m pyhabot.simple_cli rescrape 1
   ```

## Security Considerations

- Keep webhook URLs secret
- Use environment variables for webhook URLs in production
- Regularly rotate webhook URLs if needed
- Monitor webhook usage in Discord server settings

## Files Created for Testing

- `test_webhook.py` - Standalone webhook test script
- `test_webhook_docker.sh` - Docker testing automation script
- `docker-compose.test.yml` - Docker compose for testing
- `test/webhook-server.conf` - Nginx configuration for local test server
- `WEBHOOK_TESTING.md` - This documentation file