# PYHABOT Architecture

Updated: 2025-11-02

## Purpose
PYHABOT is an async Python bot that monitors HardverApró (Hungarian classified ads site) search result pages. It scrapes ads, tracks new listings and price changes, and sends notifications via Discord, terminal interface, HTTP API, or advanced webhook integrations. Data is persisted in TinyDB JSON files.

**Core Purpose**: Watch specific search URLs, notify users of new ads and price changes via multiple chat integrations, REST API, and webhook endpoints.

## Deployment Options

### 1. CLI Mode (Traditional)
- Background scraping with console notifications
- Command-line interface for watch management
- Discord/Telegram integration for notifications

### 2. API Mode (New)
- RESTful HTTP API for web integrations
- Interactive OpenAPI documentation at `/docs`
- Background job processing with status tracking

### 3. Hybrid Mode (Recommended)
- **Both CLI and API run simultaneously**
- Shared domain services for consistency
- CLI handles background scraping
- API provides HTTP interface for management
- Single database, job queue, and configuration

## High-level flow

### CLI Mode Flow
1. An integration (Discord/Telegram/Terminal) receives a message.
2. Pyhabot parses it as a command (prefix default `!`) using `CommandHandler`.
3. Commands update config or the watch list in TinyDB, or return information to the user.
4. A background task runs forever, checking which watches are due, scraping ads with jittered intervals and randomized User-Agent.
5. New ads are sent as notifications; existing ads update price history and can trigger price-change alerts.

### API Mode Flow
1. HTTP client makes REST API call to FastAPI endpoints.
2. API routes validate requests using Pydantic models.
3. Background jobs are queued for async operations (scraping, webhook testing).
4. Job queue processes tasks with status tracking and error handling.
5. Responses return JSON with operation results and job status.

### Hybrid Mode Flow
- **Shared Services**: Both CLI and API use the same domain services and repositories
- **Unified Data**: Single TinyDB database for watches and advertisements
- **Coordinated Processing**: CLI handles background scraping, API provides management interface

```
CLI Flow:
[User] -> [Integration] -> (MessageBase) -> [Pyhabot._on_message]
                                    |-> [CommandHandler] -> [ConfigHandler / DatabaseHandler]

API Flow:
[HTTP Client] -> [FastAPI] -> [Pydantic Models] -> [Job Queue] -> [Domain Services]

Background Processing:
[SchedulerRunner] -> [ScraperPort] -> [RepoPort] -> [NotifierPort / WebhookNotifier]
```

## Project Structure
```
src/pyhabot/                    # Main package
  simple_app.py               # CLI application entry point
  simple_cli.py               # Command-line interface
  simple_config.py            # Configuration management
  logging.py                  # Centralized logging setup
  domain/                     # Domain layer (Hexagonal Architecture)
    models.py                 # Business entities (Watch, Advertisement, NotificationTarget)
    ports.py                  # Abstract contracts (ScraperPort, RepoPort, NotifierPort)
    services.py               # Business logic (WatchService, AdvertisementService, NotificationService)
  adapters/                   # Infrastructure layer
    api/                      # HTTP API adapters
      watch_api.py           # Watch CRUD endpoints
      job_api.py             # Job status and management
      health_api.py          # Health check endpoints
      webhook_api.py         # Webhook testing and configuration
    integrations/             # Chat platform implementations
      integration_base.py     # Abstract base classes
      discord.py             # Discord client (discord.py 2.5.0)
      terminal.py            # Simple REPL for testing
    notifications/           # Notification adapters
      webhook_notifier.py     # Advanced webhook support with retry logic
    repos/                   # Data persistence adapters
      tinydb_repo.py         # TinyDB implementation of RepoPort
    scraping/                # Web scraping adapters
      hardverapro_scraper.py # HardverApró scraper implementation
  api/                        # FastAPI application
    main.py                  # FastAPI app with CORS and lifecycle
    models.py                # Pydantic models for API requests/responses
    job_queue.py             # In-memory job queue with worker
    job_manager.py           # Global job queue manager
    dependencies.py          # Dependency injection setup
    exceptions.py            # Custom API exceptions
  scheduler/                  # Background processing
    runner.py                # Scheduler runner with jitter and backoff
run.py                        # Legacy entry point (CLI mode)
run_api.py                   # API server runner for development
start_both.sh                # Startup script for CLI + API mode
```

## Key Data Structures

### Domain Models (Hexagonal Architecture)
- **Watch** (Domain Entity)
  - id: int (doc_id)
  - url: str
  - last_checked: float (epoch seconds)
  - notifyon: Optional[NotificationTarget]
  - webhook: Optional[str]
  - Methods: `create_new()`, `needs_check()`

- **Advertisement** (Domain Entity)
  - id: int (source ad id; used as doc_id)
  - title, url, price, city, date, pinned
  - seller_name, seller_url, seller_rates, image
  - watch_id: int
  - active: bool
  - prev_prices: list[int]
  - price_alert: bool

- **NotificationTarget** (Value Object)
  - channel_id: str
  - integration: NotificationType (WEBHOOK)
  - webhook_url: Optional[str]

### API Models (Pydantic)
- **WatchRequest/Response**: HTTP API request/response models
- **SetWebhookRequest**: Advanced webhook configuration
- **WebhookTestRequest/Response**: Webhook testing with validation
- **JobResponse**: Background job status and results
- **HealthResponse**: Service health status

### Database Schema (TinyDB)
- **watches table**: Watch configurations
- **advertisements table**: Advertisement data with price history
- **config table**: Application configuration

## Key Technologies & Dependencies
- **Python 3.11+** with async/await patterns
- **discord.py 2.5.0** - Discord integration
- **fastapi 0.104.0** - HTTP API framework with auto OpenAPI docs
- **uvicorn 0.24.0** - ASGI server for FastAPI
- **pydantic 2.4.0** - Data validation and serialization
- **aiohttp** - Async HTTP client for scraping
- **beautifulsoup4 4.13.3** - HTML parsing
- **tinydb 4.8.2** - JSON-based document database
- **python-dotenv 1.0.1** - Environment configuration

### Development Tools
- **pytest 7.4.0** - Testing framework with async support
- **pytest-cov 4.1.0** - Coverage reporting
- **mypy 1.5.0** - Static type checking
- **ruff 0.1.0** - Linting and formatting
- **black 23.7.0** - Code formatting

### Deployment
- **Docker** - Containerized deployment with multi-stage builds
- **Docker Compose** - Orchestration with health checks
- **Poetry** - Dependency management and packaging

## Architecture Patterns

### Hexagonal Architecture (Ports & Adapters)
- **Domain Layer**: Pure business logic with no external dependencies
  - `models.py`: Business entities (Watch, Advertisement)
  - `ports.py`: Abstract contracts (ScraperPort, RepoPort, NotifierPort)
  - `services.py`: Business logic (WatchService, AdvertisementService)
- **Adapter Layer**: Infrastructure implementations
  - `adapters/scraping/`: Web scraping implementations
  - `adapters/repos/`: Data persistence implementations
  - `adapters/integrations/`: Chat platform implementations
  - `adapters/notifications/`: Notification implementations
  - `adapters/api/`: HTTP API implementations

### Async-First Design
- All I/O operations use async/await
- Single background task with configurable intervals and jitter
- aiohttp.ClientSession lifecycle managed by integration's ready event
- Job queue for async API operations with status tracking

### Integration Pattern
- `IntegrationBase` defines abstract contract for message handling
- `MessageBase` provides common message interface across platforms
- Concrete integrations (Discord/Terminal) implement platform-specific clients
- Selected via `INTEGRATION` env var at startup

### Data Flow
```
CLI Mode:
User Message → Integration → Pyhabot._on_message → CommandHandler
                                                  ↓
                                    ConfigHandler / DatabaseHandler
                                                  ↓
                                    Integration.send_message_to_channel

API Mode:
HTTP Request → FastAPI → Pydantic Models → Job Queue → Domain Services
                                                  ↓
                                    JSON Response + Job Status

Background: SchedulerRunner → ScraperPort → RepoPort → NotifierPort
                                                      ↓
                          handle_new_ads / send_price_change_alert
```

## Error Handling and Logging
- **Centralized Logging**: `pyhabot.logging` module with structured logging
- **Configurable Levels**: DEBUG, INFO, WARNING, ERROR via LOG_LEVEL env var
- **API Exception Handling**: Custom exceptions with proper HTTP status codes
- **Retry Logic**: Exponential backoff with jitter for network operations
- **Webhook Resilience**: Smart retry policies (4xx no retry, 5xx with backoff)
- **Job Queue Error Handling**: Failed jobs tracked with error messages
- **Graceful Degradation**: System continues operating when individual components fail

### Logging Configuration
```python
# Environment-based configuration
LOG_LEVEL=INFO          # Default logging level
PYTHONUNBUFFERED=1      # Real-time log output
```

## Known Limitations & Tech Debt

### Scraper Limitations
- **Brittle HTML Parsing**: Tightly coupled to HardverApró HTML structure (class names like `uad-list`). Will break if site changes.
- **No Rate Limiting**: Only basic delays; no per-domain throttling
- **Robots.txt Compliance**: Checked at startup but not enforced per-path or crawl-delay

### Data Storage Limitations
- **TinyDB Concurrency**: Single JSON file, no locking—avoid concurrent writes
- **No Indexing**: Performance issues with large datasets
- **Data Migration**: No built-in migration system for schema changes

### Integration Issues
- **Message Formatting**: Inconsistent Markdown escaping across platforms
- **Mixed Language**: Commands and help mostly in Hungarian
- **Session Management**: Potential aiohttp session leaks on unexpected shutdown

### Testing Gaps
- **No Unit Tests**: Missing tests for parsers (`convert_date`, `convert_price`, `scrape_ads`)
- **No CI Pipeline**: No automated testing or deployment
- **Limited Coverage**: Terminal integration has limited testing coverage

### API Limitations
- **In-Memory Job Queue**: Jobs lost on restart; no persistence
- **No Authentication**: API endpoints are open (acceptable for current use case)
- **Rate Limiting**: No API rate limiting implemented

## Suggested Improvements (Tech Debt)

### High Priority
- **Add Unit Tests**: HTML fixtures for parsers, domain services, and API endpoints
- **SQLite Migration**: Replace TinyDB for better concurrency and indexing
- **Message Formatting**: Centralize with proper Markdown escaping per platform
- **Rate Limiting**: Implement per-domain throttling and robots.txt crawl-delay adherence

### Medium Priority
- **Job Persistence**: Replace in-memory queue with Redis or database
- **API Authentication**: Add API key or token-based authentication
- **Monitoring**: Add health checks, metrics, and alerting
- **Graceful Shutdown**: Proper cleanup of aiohttp sessions and background tasks

### Low Priority
- **Internationalization**: English localization or i18n framework
- **Type Safety**: Add mypy configuration and CI type checking
- **Documentation**: API documentation with examples and tutorials
- **Performance**: Caching layer for frequently accessed data

### When Modifying Code
1. **Scraper changes**: Test against live HardverApró pages; site structure may vary
2. **Integration changes**: Test message formatting per platform (Markdown escaping differs)
3. **Database changes**: Ensure backward compatibility with existing JSON files
4. **Config changes**: Update defaults and provide migration path
5. **Commands**: Update help text in Hungarian and consider English localization

## Command Reference

### CLI Commands
- `!help` - Show commands
- `!add <url>` - Add watch
- `!remove <id>` - Remove watch
- `!list` - List watches
- `!notifyon <id>` - Enable notifications for watch
- `!rescrape [id]` - Force re-scrape
- `!setwebhook <id> <url>` - Set webhook for watch
- `!setpricealert <adid>` - Enable price alerts for ad

### HTTP API Endpoints
- `POST /api/v1/watches` - Create watch
- `GET /api/v1/watches` - List watches
- `GET /api/v1/watches/{id}` - Get watch
- `DELETE /api/v1/watches/{id}` - Remove watch
- `PUT /api/v1/watches/{id}/webhook` - Set webhook
- `DELETE /api/v1/watches/{id}/webhook` - Remove webhook
- `GET /api/v1/watches/{id}/ads` - Get watch ads
- `POST /api/v1/jobs/watches/{id}/rescrape` - Force re-scraping (async)
- `GET /api/v1/jobs/{id}` - Get job status
- `GET /api/v1/jobs` - List all jobs
- `DELETE /api/v1/jobs/{id}` - Cancel job
- `POST /api/v1/webhooks/test` - Test any webhook URL
- `GET /api/v1/webhooks/watches/{id}/config` - Get webhook configuration
- `POST /api/v1/webhooks/watches/{id}/test` - Test watch webhook
- `GET /api/v1/webhooks/types` - Get supported webhook types
- `GET /health` - Health check
- `GET /version` - API version info
- `GET /ping` - Simple connectivity test

## Environment Variables
- `INTEGRATION`: discord | terminal (required for CLI mode)
- `DISCORD_TOKEN`: Auth token (required for Discord integration)
- `PERSISTENT_DATA_PATH`: Data directory (default: `./persistent_data`)
- `MODE`: cli | api (default: api for cloud deployments)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `API_RELOAD`: Enable auto-reload for development (default: false)

## Phase 2: Webhook Support (COMPLETED)

### Enhanced Webhook Features
- **Multi-platform support**: Discord (embeds), Slack (attachments), Generic (JSON)
- **Advanced configuration**: Custom usernames, avatars, headers, authentication
- **Retry logic**: Exponential backoff with jitter (1s → 2s → 4s, max 60s)
- **Smart error handling**: 4xx errors don't retry, 5xx errors do, respects rate limits
- **Testing tools**: API endpoints and manual testing script
- **Comprehensive documentation**: Setup guides for all platforms

### New Webhook API Endpoints
- `POST /api/v1/webhooks/test` - Test any webhook URL with validation
- `GET /api/v1/webhooks/watches/{id}/config` - Get webhook configuration and stats
- `POST /api/v1/webhooks/watches/{id}/test` - Test webhook for specific watch
- `GET /api/v1/webhooks/types` - Get supported webhook types and features

## Data Flow Diagram (ASCII)
```
CLI Mode:
+------------------+       command        +--------------------+
| User (Discord/   |  ----------------->  | Integration (SDKs) |
| Terminal)        |                      +---------+----------+
+------------------+                                |
                                                   v on_message
                                        +----------+-----------+
                                        |      Pyhabot        |
                                        |  _on_message        |
                                        +----------+----------+
                                                   |
                                                   v
                                         +---------+--------+
                                         |  CommandHandler  |
                                         +---------+--------+
                                                   |
                      +----------------------------+----------------------------+
                      |                             |                            |
                      v                             v                            v
            +---------+--------+        +----------+---------+       +----------+----------+
            |  ConfigHandler   |        | DatabaseHandler     |       | Integration.send   |
            |  (config.json)   |        | (TinyDB tables)     |       | (notify/channel)   |
            +------------------+        +---------------------+       +--------------------+

API Mode:
+------------------+      HTTP       +------------------+      Pydantic      +-----------------+
| HTTP Client      |  ------------>  | FastAPI Routes   |  ------------>  | Domain Services |
| (Browser/cURL)   |                | (OpenAPI docs)   |                | (Business Logic)|
+------------------+                +------------------+                +-----------------+
       |                                    |                                    |
       v                                    v                                    v
+------------------+                +-----------------+                +-----------------+
| JSON Response    | <------------- | Job Queue       | <------------- | RepoPort        |
| + Job Status     |   Async        | (Background)    |   Persistence | (TinyDB)        |
+------------------+                +-----------------+                +-----------------+

Background Processing (Both Modes):
+------------------+    scrape    +-----------------+    persist    +-----------------+
| SchedulerRunner |  --------->  | ScraperPort     |  --------->  | RepoPort        |
| (Jitter/Backoff)|             | (aiohttp/BS4)   |             | (TinyDB)        |
+------------------+             +-----------------+             +-----------------+
        |                                                           |
        v                                                           v
+------------------+                                            +-----------------+
| NotifierPort     | <------------------------------------------ | New Ads/Price   |
| (Discord/Webhook)|    notify                                  | Changes         |
+------------------+                                            +-----------------+
```
