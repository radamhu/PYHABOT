<p align="center">
    <img width="50%" height="auto" src="https://github.com/Patrick2562/PYHABOT/blob/master/assets/logo.png">
</p>

# PYHABOT

This fork was created to add extra features. Original repo by Patrick2562: [PYHABOT](https://github.com/Patrick2562/PYHABOT) 

**PYHABOT** is a _web scraping_ application in Python, which reviews the ads uploaded to [Hardverapró](https://hardverapro.hu) and sends notifications when a new one is published, about those that meet the conditions specified by us. It runs as a simple async Python application with console notifications and optional webhook support.

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

### Using the CLI
```bash
# Use pyhabot commands
pyhabot run                    # Start bot
pyhabot list                   # List watches  
pyhabot add-watch <url>          # Add watch
pyhabot remove <id>             # Remove watch
pyhabot set-webhook <id> <url>  # Set webhook
pyhabot rescrape <id>            # Force rescrape

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

# Set proper ownership on persistent_data directory
sudo chown -R $(id -u):$(id -g) persistent_data/

# Build and start with user mapping
docker compose --env-file .env.docker up --build -d pyhabot

# Terminal integration (Foreground mode)
docker compose --env-file .env.docker up pyhabot

# Access the container with bash if needed
docker compose --env-file .env.docker exec pyhabot bash
docker compose --env-file .env.docker exec pyhabot pyhabot list

# View logs
docker compose --env-file .env.docker logs -f pyhabot | ccze -m ansi

# Stop
docker compose --env-file .env.docker down
```




# Bot Usage

PYHABOT runs as a local Python application with background scraping. Use the CLI commands to manage your watches.

## Adding a Watch

1. Go to [Hardverapró](https://hardverapro.hu) and search for your desired product
2. Use detailed search with category, min/max price filters
3. Click KERESÉS and copy the URL from the results page
4. Add watch: `pyhabot add-watch <copied_url>`
5. Note the watch ID for other commands

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


# Features

- **Background scraping**: Continuously monitors HardverApró search URLs
- **Console notifications**: Real-time alerts for new ads and price changes
- **Webhook support**: Send notifications to Discord, Slack, or other services
- **Simple CLI**: Easy command-line interface for watch management
- **Docker support**: Containerized deployment with Docker Compose

# Commands

## CLI Commands

| Command | Description |
| :---------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| run | Start the bot with background scraping. |
| add-watch <url> | Add a new watch URL. |
| list | List all configured watches. |
| remove <watch_id> | Remove an existing watch. |
| set-webhook <watch_id> <url> | Set webhook URL for watch notifications. |
| rescrape <watch_id> | Force re-scraping for a specific watch. |
| --help | Show help for any command. |


