<p align="center">
    <img width="50%" height="auto" src="https://github.com/Patrick2562/PYHABOT/blob/master/assets/logo.png">
</p>

# PYHABOT

<p align="center">
  <a href="https://github.com/radamhu/PYHABOT/actions/workflows/build-and-push.yml">
    <img src="https://github.com/radamhu/PYHABOT/actions/workflows/build-and-push.yml/badge.svg" alt="Build Status">
  </a>
  <a href="https://github.com/radamhu/PYHABOT/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/License-GPL%20v3-blue.svg" alt="License: GPL v3">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+">
  </a>
  <a href="https://ghcr.io/radamhu/pyhabot">
    <img src="https://img.shields.io/badge/container-ghcr.io-blue" alt="Container Registry">
  </a>
  <a href="https://github.com/radamhu/PYHABOT/releases">
    <img src="https://img.shields.io/github/v/release/radamhu/PYHABOT?include_prereleases" alt="GitHub Release">
  </a>
  <a href="https://github.com/radamhu/PYHABOT/commits/master">
    <img src="https://img.shields.io/github/last-commit/radamhu/PYHABOT" alt="Last Commit">
  </a>
  <a href="https://github.com/radamhu/PYHABOT/issues">
    <img src="https://img.shields.io/github/issues/radamhu/PYHABOT" alt="GitHub Issues">
  </a>
  <a href="https://github.com/radamhu/PYHABOT">
    <img src="https://img.shields.io/github/stars/radamhu/PYHABOT?style=social" alt="GitHub Stars">
  </a>
</p>

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
# Install pyenv and pyenv-virtualenv if not already installed
# Install Python 3.12.5
pyenv install 3.12.5

# Install Poetry (if not already installed)
pyenv exec pip install poetry

# Install dependencies (virtual environment will be created automatically, dependencies installed, install project)
poetry install

# Activate virtual environment
eval $(pyenv exec poetry env activate)
# reload shell to apply changes
exec $SHELL
# Alternatively, use:
source <(pyenv exec poetry env activate)

# To deactivate the virtual environment, simply run:
poetry env deactivate

# To completely remove the virtual environment associated with your project, use:

# Option 1: Manual removal
# Find the environment path
poetry env info --path
# Then remove it (usually ~/.cache/pypoetry/virtualenvs/your-project-name)
rm -rf ~/.cache/pypoetry/virtualenvs/PYHABOT-*

# Option 2: Poetry command
# This will remove the virtual environment associated with your project
poetry env remove python

# Option 3: Remove all Poetry environments
# WARNING: This removes ALL Poetry environments
rm -rf ~/.cache/pypoetry/virtualenvs/

# Option 4: If you used pyenv with Poetry
# First deactivate the environment
pyenv deactivate
# Then remove the pyenv virtualenv
pyenv uninstall pyhabot
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

---

## Update History

This section provides a semantic-based overview of major updates and improvements to PYHABOT, organized by development phases and key features.

### Phase 3: Infrastructure & Deployment (November 2025)
**Focus**: Production readiness, CI/CD, and operational improvements

- **CI/CD Pipeline** (Nov 2025)
  - GitHub Actions workflow for automated Docker builds
  - Multi-registry support (GHCR + Docker Hub)
  - Automated testing and deployment pipeline
  - Build caching and optimization

- **API Testing & Validation** (Nov 2025)
  - Bruno API test suite integration
  - Comprehensive webhook testing capabilities
  - Health check improvements (503 bad gateway fixes)
  - API documentation updates

- **Documentation Enhancement** (Nov 2025)
  - Complete API implementation summary
  - GitHub Actions setup guide
  - Docker layer caching documentation
  - Webhook testing guide

### Phase 2: Advanced Webhook Support (October-November 2025)
**Focus**: Multi-platform integrations and robust notification system

- **Multi-Platform Webhooks** (Nov 2025)
  - Discord webhook support with rich embeds
  - Slack webhook integration with attachments
  - Generic webhook support for custom integrations
  - Custom headers and authentication support

- **Webhook Testing Tools** (Nov 2025)
  - API endpoints for webhook validation (`/api/v1/webhooks/test`)
  - Watch-specific webhook testing
  - Manual testing script for development
  - Comprehensive error handling and retry logic

- **Webhook Configuration** (Nov 2025)
  - Advanced webhook configuration options
  - Webhook type detection and validation
  - Configuration retrieval endpoints
  - Statistics and monitoring support

### Phase 1: HTTP API & Architecture Refactor (September-October 2025)
**Focus**: RESTful API, modular architecture, and cloud deployment

- **Architecture Overhaul** (Oct-Nov 2025)
  - Complete application refactoring with hexagonal architecture
  - Simplified CLI with domain services
  - Hybrid mode: CLI + API running simultaneously
  - Shared services and unified data layer

- **FastAPI Implementation** (Oct 2025)
  - RESTful HTTP API endpoints
  - Interactive OpenAPI documentation at `/docs`
  - Background job queue with async processing
  - Job status tracking and management

- **API Endpoints** (Oct 2025)
  - Watch management (CRUD operations)
  - Job control and monitoring
  - Health checks and version info
  - Webhook configuration endpoints

- **Testing Infrastructure** (Oct 2025)
  - Comprehensive test suite
  - Coverage reporting (HTML)
  - Domain service tests
  - Integration tests for webhooks

### Foundation Updates (2023-2025)
**Focus**: Core functionality, scraping improvements, and stability

- **Scraper Enhancements** (Sep 2025)
  - Anti-detection features for web scraping
  - Improved ad entry validation logic
  - Support for pinned ads display
  - Better aiohttp session management with lazy initialization

- **Docker Support** (Dec 2023)
  - Complete Docker containerization
  - Docker Compose stack for easy deployment
  - User/group mapping for permission management
  - Environment variable configuration

- **Stability Improvements** (2023-2025)
  - Site layout updates tracking
  - Message formatting improvements
  - Scraper fixes for HTML changes
  - Dependency updates and security patches

- **Original Implementation** (2021)
  - Initial bot creation by Patrick2562
  - Discord/Telegram integration
  - Basic web scraping functionality
  - Watch management system

### Key Technical Milestones

- **2025-11**: Production deployment improvements, CI/CD pipeline
- **2025-10**: Complete architecture refactor, API implementation
- **2025-09**: Scraper improvements, anti-detection features
- **2023-12**: Docker support, containerization
- **2021-05**: Initial release, basic functionality

For detailed technical documentation, see:
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Implementation Summary](docs/API_IMPLEMENTATION_SUMMARY.md)
- [Webhook Guide](docs/WEBHOOK_GUIDE.md)
- [GitHub Actions Setup](docs/GITHUB_ACTIONS_SETUP.md)
- [Docker Optimization](docs/DOCKER_LAYER_CACHING_AND_RICH_LOGGING.md)

---

## License

PYHABOT is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License v3.0** as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](LICENSE) for more details.

### License Summary

- ✅ **Commercial use** - You may use this software commercially
- ✅ **Modification** - You may modify this software
- ✅ **Distribution** - You may distribute this software
- ✅ **Patent use** - This license provides an express grant of patent rights from contributors
- ✅ **Private use** - You may use and modify the software without distributing it

**Conditions:**
- 📋 **Disclose source** - Source code must be made available when distributing
- 📋 **License and copyright notice** - Include a copy of the license and copyright notice
- 📋 **Same license** - Modifications must be released under the same license
- 📋 **State changes** - Document changes made to the code

**Limitations:**
- ❌ **Liability** - The software is provided without warranty
- ❌ **Warranty** - No warranty is provided

For the full license text, see the [LICENSE](LICENSE) file in the repository.

### Original Work

This is a fork of the original PYHABOT by Patrick2562. The original project can be found at: [https://github.com/Patrick2562/PYHABOT](https://github.com/Patrick2562/PYHABOT)

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request. By contributing to this project, you agree to license your contributions under the GPL-3.0 license.

---

<p align="center">
  Made with ❤️ by the PYHABOT community
</p>

