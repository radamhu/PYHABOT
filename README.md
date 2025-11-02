<p align="center">
    <img width="50%" height="auto" src="https://github.com/Patrick2562/PYHABOT/blob/master/assets/logo.png">
</p>

# PYHABOT

This fork was created to add extra features. Original repo by Patrick2562: [PYHABOT](https://github.com/Patrick2562/PYHABOT) 

**PYHABOT** is a _web scraping_ application in Python, which reviews the ads uploaded to [Hardverapró](https://hardverapro.hu) and sends notifications when a new one is published, about those that meet the conditions specified by us. It runs as a simple async Python application with console notifications and optional webhook support.

- **Background scraping**: Continuously monitors HardverApró search URLs
- **Console notifications**: Real-time alerts for new ads and price changes
- **Advanced webhook support**: Discord (embeds), Slack (attachments), Generic (JSON) with retry logic
- **Simple CLI**: Easy command-line interface for watch management
- **HTTP API**: RESTful endpoints for integration and web interfaces
- **Dual operation**: CLI and API run simultaneously with shared services
- **Docker support**: Containerized deployment with Docker Compose
- **Auto OpenAPI docs**: Interactive API documentation at `/docs`
- **Webhook testing**: Built-in testing tools and validation
- **Error recovery**: Exponential backoff and smart retry policies

# Quick Start

## Local development setup

### Option 1: Poetry (Recommended)
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Option 2: pip
```bash
# Or Python environment setup
pyenv install 3.12.5
pyenv virtualenv 3.12.5 pyhabot
pyenv local pyhabot
pyenv activate pyhabot

# Install project dependencies
pip install -e .
```

## Configuration

Create a `.env` file in the project root:

```bash
# Optional: Data directory (default: ./persistent_data)
PERSISTENT_DATA_PATH=/path/to/data

# Optional: Logging level (default: INFO)
LOG_LEVEL=DEBUG

# Optional: Scraping settings
SCRAPE_INTERVAL=300  # seconds
REQUEST_DELAY_MIN=1  # seconds
REQUEST_DELAY_MAX=3  # seconds
```

## Running the Bot

PYHABOT runs as a local Python application with background scraping. Use the CLI commands to manage your watches.

### CLI Commands

| Command | Description |
| :---------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| run | Start the bot with background scraping. |
| add-watch <url> | Add a new watch URL. |
| list | List all configured watches. |
| remove <watch_id> | Remove an existing watch. |
| set-webhook <watch_id> <url> | Set webhook URL for watch notifications. |
| rescrape <watch_id> | Force re-scraping for a specific watch. |
| --help | Show help for any command. |



### Using the CLI
```bash
## Running the Bot

### Using the CLI
```bash
# Use pyhabot commands
pyhabot run                    # Start bot
pyhabot list                   # List watches  
pyhabot add-watch <url>          # Add watch
pyhabot remove <id>             # Remove watch
pyhabot set-webhook <id> <url>  # Set webhook
pyhabot rescrape <id>            # Force rescrape
```

### Using the HTTP API
```bash
# Start both CLI and API
docker compose up

# API endpoints available at http://localhost:8000
# Interactive documentation at http://localhost:8000/docs
```

#### API Examples
```bash
# Create a new watch
curl -X POST http://localhost:8000/api/v1/watches \
  -H "Content-Type: application/json" \
  -d '{"url": "https://hardverapro.hu/search?param=value"}'

# List all watches
curl http://localhost:8000/api/v1/watches

# Force re-scraping
curl -X POST http://localhost:8000/api/v1/jobs/watches/1/rescrape

# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}
```

#### Testing

```bash
## Running Tests
# Run all tests
pytest
# Run with coverage
pytest --cov=pyhabot --cov-report=html
# Run specific test file
pytest tests/test_cli.py

## Code Quality
# Linting
ruff check .
# Type checking
mypy src/
# Formatting (optional)
black src/

```


### Using Docker Compose (Recommended)

This approach makes Docker use your exact user ID, preventing permission conflicts:

```bash
# Automated setup (recommended):
./scripts/setup-docker.sh

# Or manual setup:
echo "USER_ID=$(id -u)" > .env.docker
echo "GROUP_ID=$(id -g)" >> .env.docker
echo "TZ=Europe/Budapest" >> .env.docker
echo "LOG_LEVEL=INFO" >> .env.docker
echo "PERSISTENT_DATA_PATH=/data" >> .env.docker
echo "MODE=api" >> .env.docker  # Default to API mode for cloud
echo "API_HOST=0.0.0.0" >> .env.docker
echo "API_PORT=8000" >> .env.docker

# Set proper ownership on persistent_data directory
sudo chown -R $(id -u):$(id -g) persistent_data/

# Build and start with user mapping (both CLI + API)
docker compose --env-file .env.docker up --build -d pyhabot

# Terminal integration (Foreground mode)
docker compose --env-file .env.docker up pyhabot

# Access to container with bash if needed
docker compose --env-file .env.docker exec pyhabot bash
docker compose --env-file .env.docker exec pyhabot pyhabot list

# View logs
docker compose --env-file .env.docker logs -f pyhabot | ccze -m ansi

# Stop
docker compose --env-file .env.docker down

# Access API documentation
open http://localhost:8000/docs
```




## Adding a Watch

1. Go to [Hardverapró](https://hardverapro.hu) and search for your desired product
2. Use detailed search with category, min/max price filters
3. Click KERESÉS and copy the URL from the results page
4. Add watch: `pyhabot add-watch <copied_url>`
5. Note the watch ID for other commands

## HTTP API Endpoints

| Method | Endpoint | Description |
| :------ | :--------- | :---------- |
| POST | `/api/v1/watches` | Create a new watch |
| GET | `/api/v1/watches` | List all watches |
| GET | `/api/v1/watches/{id}` | Get specific watch |
| DELETE | `/api/v1/watches/{id}` | Remove watch |
| PUT | `/api/v1/watches/{id}/webhook` | Set webhook URL |
| DELETE | `/api/v1/watches/{id}/webhook` | Remove webhook |
| GET | `/api/v1/watches/{id}/ads` | Get watch advertisements |
| POST | `/api/v1/jobs/watches/{id}/rescrape` | Force re-scraping (async) |
| GET | `/api/v1/jobs/{id}` | Get job status |
| GET | `/api/v1/jobs` | List all jobs |
| DELETE | `/api/v1/jobs/{id}` | Cancel job |
| GET | `/health` | Health check |
| GET | `/version` | API version info |
| GET | `/ping` | Simple connectivity test |
| POST | `/api/v1/webhooks/test` | Test any webhook URL |
| GET | `/api/v1/webhooks/watches/{id}/config` | Get webhook configuration |
| POST | `/api/v1/webhooks/watches/{id}/test` | Test watch webhook |
| GET | `/api/v1/webhooks/types` | Get supported webhook types |


## Managing Notifications

By default, notifications are displayed in the console. You can also configure webhook notifications:

```bash
pyhabot set-webhook <watch_id> <webhook_url>  # Send notifications via webhook
```

## Initial Scanning

To scan existing ads (those posted before adding the watch):
```bash
pyhabot rescrape <watch_id>
```

### Webhook Support

PYHABOT supports multiple webhook types for real-time notifications:

- **Discord**: Rich embeds with custom usernames and avatars
- **Slack**: Formatted messages with attachments
- **Generic**: JSON payloads for custom integrations

#### Webhook Configuration Examples

```bash
# Discord webhook
curl -X PUT "http://localhost:8000/api/v1/watches/1/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://discord.com/api/webhooks/123/abc",
    "webhook_type": "discord",
    "webhook_username": "PYHABOT"
  }'

# Slack webhook
curl -X PUT "http://localhost:8000/api/v1/watches/1/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "YOUR_SLACK_WEBHOOK_URL_HERE",
    "webhook_type": "slack",
    "webhook_username": "PYHABOT"
  }'

# Generic webhook with custom headers
curl -X PUT "http://localhost:8000/api/v1/watches/1/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-api.example.com/webhooks/pyhabot",
    "webhook_type": "generic",
    "custom_headers": {
      "Authorization": "Bearer your-token"
    }
  }'
```

#### Testing Webhooks

```bash
# Test any webhook URL
curl -X POST "http://localhost:8000/api/v1/webhooks/test" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://discord.com/api/webhooks/123/abc",
    "webhook_type": "discord",
    "test_message": "Test notification from PYHABOT"
  }'

# Test webhook for a specific watch
curl -X POST "http://localhost:8000/api/v1/webhooks/watches/1/test"

# Get supported webhook types
curl -X GET "http://localhost:8000/api/v1/webhooks/types"
```

#### Manual Webhook Testing

Use the provided testing script for comprehensive webhook validation:

```bash
# Interactive webhook testing
python scripts/test_webhook_manual.py --interactive

# Direct webhook testing
python scripts/test_webhook_manual.py \
  --url "https://discord.com/api/webhooks/123/abc" \
  --type discord \
  --username "PYHABOT" \
  --verbose
```
