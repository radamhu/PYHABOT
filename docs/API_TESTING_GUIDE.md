# PYHABOT API Testing Guide

This directory contains comprehensive API testing tools and documentation for the PYHABOT application.

## 📁 Directory Structure

```
bruno/
├── pyhabot-api/                    # Bruno collection
│   ├── bruno.json                 # Collection configuration
│   ├── 01_Health_Checks.bru       # Health check endpoints
│   ├── 02_Watch_Management.bru    # Watch CRUD operations
│   ├── 03_Webhook_Management.bru  # Webhook configuration
│   ├── 04_Webhook_Testing.bru     # Webhook testing
│   ├── 05_Job_Management.bru      # Job management
│   ├── 06_Error_Handling_Tests.bru # Error scenarios
│   └── README.md                  # Bruno collection docs
├── run-tests.sh                   # Bruno test runner script
├── test-api.sh                    # curl-based test script
└── API_TESTING_GUIDE.md           # This file
```

## 🚀 Quick Start

### Option 1: Bruno (Recommended)

1. **Install Bruno**:
   ```bash
   # macOS
   brew install --cask bruno
   
   # Ubuntu/Debian
   wget https://github.com/usebruno/bruno/releases/latest/download/bruno_1.20.0_linux_amd64.deb
   sudo dpkg -i bruno_1.20.0_linux_amd64.deb
   ```

2. **Run the test runner**:
   ```bash
   ./bruno/run-tests.sh
   ```

3. **Follow the instructions** to import and run the collection

### Option 2: curl-based Testing

1. **Run the curl test script**:
   ```bash
   ./bruno/test-api.sh
   ```

2. **Run specific test categories**:
   ```bash
   ./bruno/test-api.sh health     # Health checks only
   ./bruno/test-api.sh watches    # Watch management
   ./bruno/test-api.sh webhooks   # Webhook testing
   ./bruno/test-api.sh jobs       # Job management
   ./bruno/test-api.sh errors     # Error handling
   ```

## 📋 Test Coverage

### ✅ Health Checks
- **Health Endpoint**: `/health` - Service status and component health
- **Ping**: `/ping` - Simple connectivity test
- **Version**: `/version` - API version information

### ✅ Watch Management
- **Create Watch**: `POST /api/v1/watches` - Add new monitoring watch
- **List Watches**: `GET /api/v1/watches` - Get all watches
- **Get Watch**: `GET /api/v1/watches/{id}` - Get specific watch details
- **Delete Watch**: `DELETE /api/v1/watches/{id}` - Remove watch
- **Validation**: URL validation, duplicate detection, error handling

### ✅ Webhook Management
- **Set Discord Webhook**: Configure Discord notifications with embeds
- **Set Slack Webhook**: Configure Slack notifications with attachments
- **Set Generic Webhook**: Configure HTTP webhook with custom headers
- **Get Configuration**: Retrieve webhook settings and statistics
- **Remove Webhook**: Remove webhook configuration

### ✅ Webhook Testing
- **Platform Testing**: Discord, Slack, Generic webhook formats
- **Custom Headers**: Test webhook with custom authentication headers
- **Error Handling**: Invalid URLs, network failures, retry logic
- **Watch-specific Tests**: Test webhooks for specific watches
- **Webhook Types**: Get supported webhook types and features

### ✅ Job Management
- **Force Rescrape**: Trigger immediate scraping for watches
- **List Jobs**: View all background jobs and their status
- **Job Status**: Check specific job details and progress
- **Cancel Jobs**: Cancel running background jobs
- **Watch Ads**: Retrieve advertisements for specific watches

### ✅ Error Handling
- **Invalid IDs**: Test with invalid watch and job IDs
- **Invalid JSON**: Test malformed request bodies
- **Missing Fields**: Test requests missing required data
- **Invalid Types**: Test with invalid webhook types
- **URL Validation**: Test with invalid URL formats

## 🔧 Configuration

### Environment Variables

Both testing tools support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8000` | API base URL |
| `API_VERSION` | `api/v1` | API version prefix |
| `WATCH_ID` | `1` | Default watch ID for tests |
| `DOCKER_COMPOSE_FILE` | `.env.docker` | Docker compose env file |

### Bruno Environment

The Bruno collection includes these variables:

```json
{
  "baseUrl": "http://localhost:8000",
  "apiVersion": "api/v1",
  "watchId": "1",
  "testHardveraproUrl": "https://hardverapro.hu/vegyseg/monitorok",
    "testDiscordWebhook": "https://discord.com/api/webhooks/YOUR_CHANNEL_ID/YOUR_TOKEN",
  "testSlackWebhook": "YOUR_SLACK_WEBHOOK_URL_HERE"
}
```

## 🧪 Running Tests

### Bruno Collection

1. **Import Collection**:
   - Open Bruno
   - Click "Import Collection"
   - Navigate to `bruno/pyhabot-api/`
   - Select `bruno.json`

2. **Configure Environment**:
   - Update `baseUrl` if needed
   - Replace webhook URLs with actual endpoints
   - Adjust test URLs as needed

3. **Run Tests**:
   - Individual requests: Click play button
   - Full collection: Select collection → "Run Collection"
   - View results in real-time

### curl Script Examples

```bash
# Run all tests
./bruno/test-api.sh

# Run specific categories
./bruno/test-api.sh health
./bruno/test-api.sh watches
./bruno/test-api.sh webhooks

# Custom base URL
BASE_URL=http://localhost:3000 ./bruno/test-api.sh
```

## 📊 Test Results Interpretation

### Success Indicators
- ✅ **HTTP 2xx**: Successful request
- ✅ **Green checkmarks**: Bruno test passed
- ✅ **Valid response structure**: All required fields present

### Common HTTP Status Codes
- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Error Scenarios
- **Connection refused**: API server not running
- **Authentication errors**: Invalid API keys/tokens
- **Rate limiting**: Too many requests
- **Network timeouts**: Webhook endpoint unreachable

## 🔍 API Endpoints Reference

### Base URL: `http://localhost:8000`

#### Health & Info
- `GET /health` - Service health status
- `GET /ping` - Simple connectivity test
- `GET /version` - API version information

#### Watches (`/api/v1/watches`)
- `POST /` - Create new watch
- `GET /` - List all watches
- `GET /{id}` - Get specific watch
- `DELETE /{id}` - Delete watch
- `PUT /{id}/webhook` - Set webhook configuration
- `DELETE /{id}/webhook` - Remove webhook
- `GET /{id}/ads` - Get watch advertisements

#### Webhooks (`/api/v1/webhooks`)
- `POST /test` - Test webhook URL
- `GET /types` - Get supported webhook types
- `GET /watches/{id}/config` - Get webhook configuration
- `POST /watches/{id}/test` - Test watch webhook

#### Jobs (`/api/v1/jobs`)
- `GET /` - List all jobs
- `GET /{id}` - Get job status
- `DELETE /{id}` - Cancel job
- `POST /watches/{id}/rescrape` - Force rescrape

## 🛠️ Customization

### Adding New Tests

#### Bruno Collection
1. Create new `.bru` file or add to existing
2. Use Bruno's request builder
3. Add test scripts:
   ```javascript
   bru.test('Status is 200', () => {
     bru.expect(res.getStatus()).toBe(200);
   });
   
   bru.test('Response has required fields', () => {
     const body = res.getBody();
     bru.expect(body).toHaveProperty('id');
   });
   ```

#### curl Script
1. Add new test function to `test-api.sh`
2. Add to main execution flow
3. Add command line option handling

### Test Data

#### Sample Webhook URLs
```bash
# Discord
https://discord.com/api/webhooks/YOUR_CHANNEL_ID/YOUR_TOKEN

# Slack
YOUR_SLACK_WEBHOOK_URL_HERE

# Generic (for testing)
https://httpbin.org/post
https://webhook.site/your-unique-url
```

#### Sample HardverApró URLs
```bash
https://hardverapro.hu/vegyseg/monitorok
https://hardverapro.hu/vegyseg/laptop-notebook
https://hardverapro.hu/vegyseg/telefon-mobil
```

## 🐛 Troubleshooting

### Common Issues

1. **API Not Running**:
   ```bash
   docker compose --env-file .env.docker up --build -d pyhabot
   docker compose --env-file .env.docker logs pyhabot
   ```

2. **Connection Refused**:
   - Check if API is running: `curl http://localhost:8000/health`
   - Verify port configuration
   - Check firewall settings

3. **Bruno Not Opening Collection**:
   - Ensure Bruno is installed correctly
   - Manually import: File → Import Collection
   - Check file permissions

4. **Webhook Tests Failing**:
   - Verify webhook URLs are correct
   - Check network connectivity
   - Test with `https://httpbin.org/post` first

5. **Test Data Issues**:
   - Clear existing data: `docker compose down -v`
   - Restart with fresh data: `docker compose up --build -d`
   - Check database status in API health endpoint

### Debug Commands

```bash
# Check API health
curl http://localhost:8000/health

# View API logs
docker compose --env-file .env.docker logs -f pyhabot

# Check container status
docker compose ps

# Restart API
docker compose --env-file .env.docker restart pyhabot

# Test specific endpoint
curl -X POST http://localhost:8000/api/v1/watches \
  -H "Content-Type: application/json" \
  -d '{"url": "https://hardverapro.hu/vegyseg/monitorok"}'
```

## 📚 Additional Resources

- **PYHABOT API Documentation**: http://localhost:8000/docs
- **Bruno Documentation**: https://docs.usebruno.com/
- **HardverApró**: https://hardverapro.hu/
- **Project Repository**: https://github.com/radamhu/PYHABOT
- **Docker Documentation**: https://docs.docker.com/

## 🤝 Contributing

When adding new tests:
1. Follow existing naming conventions
2. Include both positive and negative test cases
3. Add comprehensive test scripts
4. Update documentation
5. Test with both Bruno and curl scripts

## 📝 Notes

- Tests are designed to work with the current API version
- Some tests may require actual webhook URLs for full functionality
- Webhook tests use example URLs - replace with real endpoints
- API should be running before executing tests
- Check the API documentation for the most current endpoint information