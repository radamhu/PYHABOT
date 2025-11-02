# PYHABOT API Bruno Collection

This directory contains a comprehensive Bruno API testing collection for the PYHABOT application.

## 📁 Collection Structure

```
bruno/pyhabot-api/
├── bruno.json                    # Collection configuration and environment variables
├── 01_Health_Checks.bru          # Basic health and connectivity endpoints
├── 02_Watch_Management.bru       # CRUD operations for watches
├── 03_Webhook_Management.bru    # Webhook configuration endpoints
├── 04_Webhook_Testing.bru        # Webhook testing functionality
├── 05_Job_Management.bru         # Background job management
├── 06_Error_Handling_Tests.bru   # Error scenarios and edge cases
└── README.md                     # This file
```

## 🚀 Getting Started

### Prerequisites
- [Bruno API Client](https://www.usebruno.com/) installed
- PYHABOT API server running (default: `http://localhost:8000`)

### Setup Instructions

1. **Install Bruno** if you haven't already:
   ```bash
   # macOS
   brew install --cask bruno
   
   # Ubuntu/Debian
   wget https://github.com/usebruno/bruno/releases/latest/download/bruno_1.20.0_linux_amd64.deb
   sudo dpkg -i bruno_1.20.0_linux_amd64.deb
   
   # Or download from https://www.usebruno.com/downloads
   ```

2. **Start PYHABOT API**:
   ```bash
   docker compose --env-file .env.docker up --build -d pyhabot
   ```

3. **Open Bruno** and import the collection:
   - Open Bruno application
   - Click "Import Collection"
   - Navigate to `/home/ferko/Documents/PYHABOT/bruno/pyhabot-api`
   - Select the `bruno.json` file

4. **Configure Environment**:
   - The collection includes pre-configured environment variables
   - Modify `baseUrl` if your API runs on a different host/port
   - Update webhook URLs with your actual webhook endpoints

## 📋 Test Categories

### 1. Health Checks (`01_Health_Checks.bru`)
- **Health Check**: `/health` - Basic service health
- **Ping**: `/ping` - Simple connectivity test
- **Version Info**: `/version` - API version information

### 2. Watch Management (`02_Watch_Management.bru`)
- **Create Watch**: `POST /api/v1/watches` - Add new monitoring watch
- **List Watches**: `GET /api/v1/watches` - Get all watches
- **Get Watch**: `GET /api/v1/watches/{id}` - Get specific watch
- **Delete Watch**: `DELETE /api/v1/watches/{id}` - Remove watch
- **Validation tests** for invalid URLs and duplicate watches

### 3. Webhook Management (`03_Webhook_Management.bru`)
- **Set Discord Webhook**: Configure Discord notifications
- **Set Slack Webhook**: Configure Slack notifications
- **Set Generic Webhook**: Configure generic HTTP webhook
- **Get Webhook Config**: Retrieve webhook configuration
- **Remove Webhook**: Remove webhook configuration

### 4. Webhook Testing (`04_Webhook_Testing.bru`)
- **Test Discord Webhook**: Send test Discord notification
- **Test Slack Webhook**: Send test Slack message
- **Test Generic Webhook**: Send test HTTP request
- **Custom Headers**: Test webhook with custom headers
- **Error Handling**: Test invalid webhook URLs
- **Watch-specific Tests**: Test webhooks for specific watches

### 5. Job Management (`05_Job_Management.bru`)
- **Force Rescrape**: Trigger immediate scraping for a watch
- **List Jobs**: Get all background jobs
- **Get Job Status**: Check specific job status
- **Cancel Job**: Cancel running job
- **Get Watch Ads**: Retrieve advertisements for a watch

### 6. Error Handling (`06_Error_Handling_Tests.bru`)
- **Invalid IDs**: Test with invalid watch/job IDs
- **Invalid JSON**: Test malformed request bodies
- **Missing Fields**: Test requests missing required data
- **Invalid Types**: Test with invalid webhook types
- **URL Validation**: Test with invalid URL formats

## 🔧 Environment Variables

The collection includes these configurable variables:

| Variable | Default Value | Description |
|----------|--------------|-------------|
| `baseUrl` | `http://localhost:8000` | API base URL |
| `apiVersion` | `api/v1` | API version prefix |
| `watchId` | `1` | Test watch ID (auto-updated) |
| `testHardveraproUrl` | `https://hardverapro.hu/vegyseg/monitorok` | Test HardverApró URL |
| `testDiscordWebhook` | `https://discord.com/api/webhooks/YOUR_CHANNEL_ID/YOUR_TOKEN` | Test Discord webhook |
| `testSlackWebhook` | `YOUR_SLACK_WEBHOOK_URL_HERE` | Test Slack webhook |

## 🧪 Running Tests

### Individual Tests
1. Open any `.bru` file in Bruno
2. Click the play button next to individual requests
3. View results in the response panel

### Full Collection
1. Select the collection in the left sidebar
2. Click "Run Collection" or press `Cmd/Ctrl + R`
3. Monitor test results in real-time

### Test Scripts
Each request includes automated test scripts that:
- Validate HTTP status codes
- Check response structure
- Store variables for subsequent tests
- Log important information

## 📊 Test Data

### Sample Webhook URLs
Replace the test webhook URLs with your actual endpoints:

**Discord:**
```
https://discord.com/api/webhooks/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN
```

**Slack:**
```
YOUR_SLACK_WEBHOOK_URL_HERE
```

**Generic HTTP:**
```
https://httpbin.org/post  # For testing
https://your-webhook-endpoint.com/notify
```

### Sample HardverApró URLs
```
https://hardverapro.hu/vegyseg/monitorok
https://hardverapro.hu/vegyseg/laptop-notebook
https://hardverapro.hu/vegyseg/telefon-mobil
```

## 🔍 Test Results Interpretation

### Success Indicators
- ✅ **Green checkmark**: Test passed
- **Status 200/201**: Successful HTTP response
- **Response validation**: All required fields present

### Failure Indicators
- ❌ **Red X**: Test failed
- **Status 4xx**: Client error (validation, authentication)
- **Status 5xx**: Server error
- **Test script failures**: Response structure issues

### Common Issues
1. **Connection refused**: API server not running
2. **404 Not Found**: Invalid endpoint or resource ID
3. **422 Validation**: Invalid request data
4. **Webhook failures**: Invalid webhook URLs or network issues

## 🛠️ Customization

### Adding New Tests
1. Create new `.bru` files or add to existing ones
2. Use Bruno's request builder for complex requests
3. Add test scripts using JavaScript
4. Update environment variables as needed

### Test Scripts Examples
```javascript
// Status validation
bru.test('Status is 200', () => {
  bru.expect(res.getStatus()).toBe(200);
});

// Response structure validation
bru.test('Response has required fields', () => {
  const body = res.getBody();
  bru.expect(body).toHaveProperty('id');
  bru.expect(body).toHaveProperty('url');
});

// Variable storage
bru.test('Store watch ID', () => {
  const body = res.getBody();
  bru.setVar('watchId', body.id.toString());
});
```

## 📝 Notes

- Tests are designed to be run in sequence (some depend on previous results)
- Webhook tests use example URLs - replace with real endpoints for actual testing
- Some tests may fail if the API doesn't have sample data
- Check the API documentation at `http://localhost:8000/docs` for detailed endpoint information

## 🐛 Troubleshooting

### Common Issues
1. **"Connection refused"**: Start the API server
2. **"404 Not Found"**: Check API version and endpoint paths
3. **"422 Validation Error"**: Verify request body format
4. **Webhook timeouts**: Check network connectivity and webhook URLs

### Debug Tips
- Use Bruno's console for detailed error messages
- Check API server logs: `docker compose logs pyhabot`
- Verify environment variables in Bruno settings
- Test endpoints manually with curl or Postman for comparison

## 📚 Additional Resources

- [PYHABOT API Documentation](http://localhost:8000/docs)
- [Bruno Documentation](https://docs.usebruno.com/)
- [HardverApró Website](https://hardverapro.hu/)
- [Project Repository](https://github.com/radamhu/PYHABOT)