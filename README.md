<p align="center">
    <img width="50%" height="auto" src="https://github.com/Patrick2562/PYHABOT/blob/master/assets/logo.png">
</p>

# PYHABOT

This fork was created to add extra features. Original repo by Patrick2562: [PYHABOT](https://github.com/Patrick2562/PYHABOT) 

**PYHABOT** is a _web scraping_ application in Python, which reviews the ads uploaded to [Hardverapróra](https://hardverapro.hu) and sends notifications when a new one is published, about those that meet the conditions specified by us. It also has several integrations that allow you to add and delete the products you want to search through commands.

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
# Required: Integration type
INTEGRATION=discord  # or telegram, terminal

# Required: Authentication token for your integration
DISCORD_TOKEN=your_discord_bot_token
# TELEGRAM_TOKEN=your_telegram_bot_token

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
# Run with integration from environment
pyhabot run
pyhabot --help
pyhabot run --help
pyhabot add-watch --help

# Or specify integration explicitly
pyhabot run --integration discord
pyhabot run --integration telegram
pyhabot run --integration terminal

# Add a new watch
pyhabot add-watch "https://hardverapro.hu/aprok/mobil/tablet/android_tablet/10_felett/keres.php?stext=Samsung+Galaxy+Tab&stcid_text=&stcid=&stmid_text=&stmid=&minprice=&maxprice=&cmpid_text=&cmpid=&usrid_text=&usrid=&__buying=1&__buying=0&stext_none=&__brandnew=1&__brandnew=0"

# List watches (coming soon)
pyhabot list

# Force re-scrape (coming soon)
pyhabot rescrape <watch_id>


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


```bash
# Test the Docker setup (Optional)
./test-docker.sh

# Build and start Detached mode (the -d flag)
docker compose up -d pyhabot

# Recreate container (if .env or settings changed), even if their configuration and image haven't changed
docker compose up -d --force-recreate pyhabot

# Terminal integration (Foreground mode)
docker-compose up pyhabot

# Discord integration
INTEGRATION=discord DISCORD_TOKEN=your_token docker-compose up pyhabot

# Telegram integration  
INTEGRATION=telegram TELEGRAM_TOKEN=your_token docker-compose up pyhabot

# Access the container with bash if needed
docker compose exec pyhabot bash

# View logs
docker compose logs -f pyhabot | ccze -m ansi

# Stop
docker compose down

# Check what UID/GID the pyhabot user has in the container:
docker run --rm pyhabot:latest id pyhabot

# If the user has UID/GID 999, not 1000. Fix the ownership:
sudo chown -R 999:999 persistent_data/
ls -la persistent_data/

# Now let's try running the container again:
docker compose up pyhabot

```


# Bot Usage

After inviting the bot to your server/channel, you can use the following commands. All commands require the prefix (default: `!`).

## Adding a Watch

1. Go to [Hardverapró](https://hardverapro.hu) and search for your desired product
2. Use detailed search with category, min/max price filters
3. Click KERESÉS and copy the URL from the results page
4. Send to bot: `!add <copied_url>`
5. Note the watch ID for other commands

## Managing Notifications

By default, notifications go to the channel where the command was issued. You can change this:

```bash
!notifyon <watch_id>  # Set current channel for notifications
!setwebhook <watch_id> <webhook_url>  # Send notifications via webhook
```

## Initial Scanning

To scan existing ads (those posted before adding the watch):
```bash
!rescrape <watch_id>
```


# Integrations

| Integration | Description | Setup |
| :---------- | :---------- | :----- |
| discord | Discord bot | Create bot at Discord Developer Portal, invite to server |
| telegram | Telegram bot | Create bot via BotFather, add to chat/group |
| terminal | Local terminal | For testing and local use only |

# Commands

## Chat Commands (Legacy)

All commands require the prefix (default: `!`):

| Command | Description |
| :---------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| help | List available commands. |
| add <url> | Add a new watch. |
| remove <watch_id> | Remove an existing watch. |
| list | List all watches. |
| info <watch_id> | Get watch information. |
| seturl <watch_id> <url> | Modify watch URL. |
| notifyon <watch_id> | Set current channel for notifications. |
| setwebhook <watch_id> <url> | Set webhook for watch. |
| unsetwebhook <watch_id> | Remove webhook from watch. |
| rescrape <watch_id> | Clear saved ads and re-scrape. |
| listads <watch_id> | Get ads for watch. |
| adinfo <ad_id> | Get advertisement information. |
| setpricealert <ad_id> | Enable price change alerts for ad. |
| unsetpricealert <ad_id> | Disable price change alerts for ad. |
| settings | Get bot settings. |
| setprefix <prefix> | Change command prefix. |
| setinterval <interval> | Set scrape interval in seconds. |


