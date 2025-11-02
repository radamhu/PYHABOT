# PYHABOT Webhook Guide

## Overview

PYHABOT supports webhook notifications for real-time alerts about new advertisements and price changes. Webhooks allow you to integrate PYHABOT with various platforms like Discord, Slack, or custom HTTP endpoints.

## Supported Webhook Types

### 1. Discord Webhooks
- **Format**: Discord webhook format with embed support
- **Features**: Custom username, avatar, embeds, TTS support
- **Documentation**: [Discord Webhook Documentation](https://discord.com/developers/docs/resources/webhook)

### 2. Slack Webhooks
- **Format**: Slack incoming webhook format
- **Features**: Custom username, icon, attachments
- **Documentation**: [Slack Webhook Documentation](https://api.slack.com/messaging/webhooks)

### 3. Generic Webhooks
- **Format**: JSON payload with standard fields
- **Features**: Custom headers, flexible payload structure
- **Use Case**: Custom integrations, monitoring systems, automation tools

## Configuration

### Basic Webhook Setup

1. **Create a watch** with webhook URL:
```bash
curl -X POST "http://localhost:8000/api/v1/watches" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://hardverapro.hu/search?param=value",
    "webhook_url": "https://discord.com/api/webhooks/123/abc"
  }'
```

2. **Set webhook for existing watch**:
```bash
curl -X PUT "http://localhost:8000/api/v1/watches/1/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://discord.com/api/webhooks/123/abc",
    "webhook_type": "discord",
    "webhook_username": "PYHABOT",
    "webhook_avatar": "https://example.com/avatar.png"
  }'
```

### Advanced Webhook Configuration

#### Discord Webhook Example
```json
{
  "webhook_url": "https://discord.com/api/webhooks/123/abc",
  "webhook_type": "discord",
  "webhook_username": "PYHABOT",
  "webhook_avatar": "https://example.com/avatar.png"
}
```

#### Slack Webhook Example
```json
{
  "webhook_url": "YOUR_SLACK_WEBHOOK_URL_HERE",
  "webhook_type": "slack",
  "webhook_username": "PYHABOT"
}
```

#### Generic Webhook Example
```json
{
  "webhook_url": "https://your-api.example.com/webhooks/pyhabot",
  "webhook_type": "generic",
  "custom_headers": {
    "Authorization": "Bearer your-token",
    "X-Custom-Header": "custom-value"
  }
}
```

## API Endpoints

### Test Webhook
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/test" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://discord.com/api/webhooks/123/abc",
    "webhook_type": "discord",
    "test_message": "Test notification from PYHABOT"
  }'
```

### Get Webhook Configuration
```bash
curl -X GET "http://localhost:8000/api/v1/webhooks/watches/1/config"
```

### Test Watch Webhook
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/watches/1/test" \
  -H "Content-Type: application/json" \
  -d '{
    "test_message": "Custom test message"
  }'
```

### Get Supported Webhook Types
```bash
curl -X GET "http://localhost:8000/api/v1/webhooks/types"
```

## Notification Payloads

### New Advertisement Notification

#### Discord Format
```json
{
  "content": "🆕 Új hirdetés: Eladó laptop\n💰 Ár: 150 000 Ft\n📍 Helyszín: Budapest\n👤 Eladó: János\n🔗 https://hardverapro.hu/termek/123",
  "username": "PYHABOT",
  "embeds": []
}
```

#### Slack Format
```json
{
  "text": "🆕 Új hirdetés: Eladó laptop\n💰 Ár: 150 000 Ft\n📍 Helyszín: Budapest\n👤 Eladó: János\n🔗 https://hardverapro.hu/termek/123",
  "username": "PYHABOT",
  "attachments": []
}
```

#### Generic Format
```json
{
  "message": "🆕 Új hirdetés: Eladó laptop\n💰 Ár: 150 000 Ft\n📍 Helyszín: Budapest\n👤 Eladó: János\n🔗 https://hardverapro.hu/termek/123",
  "timestamp": "2025-11-02T13:33:00.000Z",
  "source": "PYHABOT"
}
```

### Price Change Notification

#### Discord Format
```json
{
  "content": "💸 Árváltozás: Eladó laptop\n📉 Régi ár: 160 000 Ft\n📈 Új ár: 150 000 Ft\n📍 Helyszín: Budapest\n🔗 https://hardverapro.hu/termek/123",
  "username": "PYHABOT",
  "embeds": []
}
```

#### Slack Format
```json
{
  "text": "💸 Árváltozás: Eladó laptop\n📉 Régi ár: 160 000 Ft\n📈 Új ár: 150 000 Ft\n📍 Helyszín: Budapest\n🔗 https://hardverapro.hu/termek/123",
  "username": "PYHABOT",
  "attachments": []
}
```

#### Generic Format
```json
{
  "message": "💸 Árváltozás: Eladó laptop\n📉 Régi ár: 160 000 Ft\n📈 Új ár: 150 000 Ft\n📍 Helyszín: Budapest\n🔗 https://hardverapro.hu/termek/123",
  "timestamp": "2025-11-02T13:33:00.000Z",
  "source": "PYHABOT"
}
```

## Retry Logic

Webhooks use exponential backoff with jitter for reliability:

- **Max Retries**: 3 attempts (1 initial + 2 retries)
- **Base Delay**: 1.0 second
- **Max Delay**: 60.0 seconds
- **Backoff Factor**: 2.0 (exponential)
- **Jitter**: ±25% random variation

### Retry Behavior
1. **First attempt**: Immediate
2. **Second attempt**: After ~1 second (with jitter)
3. **Third attempt**: After ~2 seconds (with jitter)
4. **Fourth attempt**: After ~4 seconds (with jitter)

### Error Handling
- **4xx Errors**: No retry (client error)
- **5xx Errors**: Retry with backoff
- **Network Errors**: Retry with backoff
- **Rate Limiting**: Respect `Retry-After` header if provided

## Testing Webhooks

### Manual Testing Script

Use the provided testing script for manual webhook validation:

```bash
# Interactive mode
python scripts/test_webhook_manual.py --interactive

# Direct testing
python scripts/test_webhook_manual.py \
  --url "https://discord.com/api/webhooks/123/abc" \
  --type discord \
  --username "PYHABOT" \
  --verbose
```

### API Testing

Test webhooks directly via the API:

```bash
# Test webhook configuration
curl -X POST "http://localhost:8000/api/v1/webhooks/test" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-webhook-url",
    "webhook_type": "discord",
    "test_message": "Test from PYHABOT API"
  }'
```

## Platform-Specific Setup

### Discord Webhook Setup

1. **Create Discord Server** (if you don't have one)
2. **Create Webhook Channel**:
   - Go to Server Settings → Integrations
   - Create Webhook
   - Choose channel and customize name/avatar
   - Copy webhook URL

3. **Configure PYHABOT**:
   ```bash
   curl -X PUT "http://localhost:8000/api/v1/watches/1/webhook" \
     -H "Content-Type: application/json" \
     -d '{
       "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN",
       "webhook_type": "discord",
       "webhook_username": "PYHABOT"
     }'
   ```

### Slack Webhook Setup

1. **Create Slack App**:
   - Go to [Slack API](https://api.slack.com/apps)
   - Create New App → From scratch
   - Add "Incoming Webhooks" feature
   - Activate Incoming Webhooks
   - Add new webhook to workspace/channel
   - Copy webhook URL

2. **Configure PYHABOT**:
   ```bash
   curl -X PUT "http://localhost:8000/api/v1/watches/1/webhook" \
     -H "Content-Type: application/json" \
     -d '{
       "webhook_url": "YOUR_SLACK_WEBHOOK_URL_HERE",
       "webhook_type": "slack",
       "webhook_username": "PYHABOT"
     }'
   ```

### Generic Webhook Setup

For custom endpoints, ensure your endpoint:

1. **Accepts POST requests** with JSON payload
2. **Returns 2xx status codes** for success
3. **Handles authentication** if required (via custom headers)
4. **Processes the payload** appropriately

Example webhook receiver (Flask):
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    print(f"Received webhook: {data}")
    
    # Process the notification
    message = data.get('message', '')
    timestamp = data.get('timestamp', '')
    
    # Your custom logic here
    
    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

## Security Considerations

### Webhook URL Security
- **Keep webhook URLs secret** - they can be used to post to your channels
- **Use HTTPS** to prevent interception
- **Rotate webhook URLs** periodically if compromised
- **Monitor webhook usage** for unusual activity

### Authentication
- **Custom headers** for API keys/tokens
- **Bearer token authentication** for generic webhooks
- **IP whitelisting** if supported by your webhook provider

### Rate Limiting
- **Respect rate limits** of webhook providers
- **Monitor retry attempts** to avoid spam
- **Configure appropriate delays** between notifications

## Troubleshooting

### Common Issues

1. **Webhook Not Triggered**
   - Check if watch has webhook configured
   - Verify webhook URL is correct
   - Check if notifications are enabled for the watch

2. **Webhook Delivery Failed**
   - Verify webhook URL is accessible
   - Check authentication credentials
   - Review error logs for specific failure reasons

3. **Rate Limiting**
   - Reduce notification frequency
   - Implement proper backoff
   - Contact provider for rate limit increases

4. **Payload Format Issues**
   - Verify webhook type matches provider
   - Check for required fields in payload
   - Test with different message formats

### Debugging

1. **Enable verbose logging** in webhook notifier
2. **Use webhook testing endpoints** to validate configuration
3. **Monitor webhook provider logs** for delivery status
4. **Check network connectivity** to webhook URLs

### Monitoring

Monitor webhook health by:
- Checking API health endpoints
- Monitoring webhook test results
- Tracking notification success/failure rates
- Setting up alerts for webhook failures

## Examples

### Complete Discord Integration

```bash
# 1. Create watch with Discord webhook
curl -X POST "http://localhost:8000/api/v1/watches" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://hardverapro.hu/search?c=notebook",
    "webhook_url": "https://discord.com/api/webhooks/123/abc"
  }'

# 2. Test the webhook
curl -X POST "http://localhost:8000/api/v1/webhooks/watches/1/test" \
  -H "Content-Type: application/json" \
  -d '{
    "test_message": "🧪 Test notification from PYHABOT"
  }'

# 3. Check webhook configuration
curl -X GET "http://localhost:8000/api/v1/webhooks/watches/1/config"
```

### Custom Integration with Headers

```bash
# Configure webhook with custom authentication
curl -X PUT "http://localhost:8000/api/v1/watches/1/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-api.example.com/webhooks/pyhabot",
    "webhook_type": "generic",
    "custom_headers": {
      "Authorization": "Bearer sk-1234567890",
      "X-Source": "pyhabot",
      "X-Environment": "production"
    }
  }'
```

## Best Practices

1. **Test webhooks before production** use
2. **Monitor webhook delivery** and success rates
3. **Implement proper error handling** in webhook receivers
4. **Use appropriate retry policies** for your use case
5. **Secure webhook URLs** and authentication credentials
6. **Document webhook payload format** for integration teams
7. **Plan for webhook provider outages** with fallback mechanisms
8. **Rate limit notifications** to avoid overwhelming receivers

## Support

For webhook-related issues:

1. Check the [API documentation](http://localhost:8000/docs)
2. Review webhook testing results
3. Examine application logs
4. Test with the manual testing script
5. Verify webhook provider documentation

For additional help, refer to the project documentation or create an issue in the repository.