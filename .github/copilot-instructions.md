# PYHABOT - GitHub Copilot Instructions

## Project Overview
PYHABOT is an async Python bot that monitors HardverApró (Hungarian classified ads site) search result pages. It scrapes ads, tracks new listings and price changes, and sends notifications via Discord or terminal interface. Data is persisted in TinyDB JSON files.

**Core Purpose**: Watch specific search URLs, notify users of new ads and price changes via multiple chat integrations.

## Project Structure
```
pyhabot/                    # Main package
  pyhabot.py               # Core orchestrator: lifecycle, background loop, notifications
  command_handler.py       # Command registry and argparse-based dispatcher
  config_handler.py        # JSON-backed configuration with immediate persistence
  database_handler.py      # TinyDB persistence for watches and advertisements
  scraper.py              # Async web scraping (aiohttp + BeautifulSoup)
  integrations/           # Chat platform implementations
    integration_base.py   # Abstract base classes (IntegrationBase, MessageBase)
    discord.py           # Discord client (discord.py 2.5.0)

    terminal.py          # Simple REPL for testing
run.py                    # Entry point: bootstraps from INTEGRATION env var
docs/                     # Architecture and analysis documentation
persistent_data/          # Runtime data (config.json, tinydb.json)
```

## Key Technologies & Dependencies
- **Python 3.11+** with async/await patterns
- **discord.py 2.5.0** - Discord integration

- **aiohttp** - Async HTTP client for scraping
- **beautifulsoup4 4.13.3** - HTML parsing
- **tinydb 4.8.2** - JSON-based document database
- **python-dotenv 1.0.1** - Environment configuration

## Architecture Patterns

### Async-First Design
- All I/O operations use async/await
- Single background task with configurable intervals and jitter
- aiohttp.ClientSession lifecycle managed by integration's ready event

### Integration Pattern
- `IntegrationBase` defines abstract contract for message handling
- `MessageBase` provides common message interface across platforms
- Concrete integrations (Discord/Terminal) implement platform-specific clients
- Selected via `INTEGRATION` env var at startup

### Data Flow
```
User Message → Integration → Pyhabot._on_message → CommandHandler
                                                  ↓
                                    ConfigHandler / DatabaseHandler
                                                  ↓
                                    Integration.send_message_to_channel

Background: Pyhabot.run_forever → scraper.scrape_ads → DatabaseHandler
                                                      ↓
                          handle_new_ads / _send_price_change_alert
```

### Command System
- Prefix-based (default `!`), configurable via `setprefix`
- Declarative registry in `COMMANDS` list
- Dynamic callback registration from `Pyhabot` methods
- Commands: help, settings, add/remove/list watches, notifyon, rescrape, etc.

## Coding Standards

### Naming Conventions
- **Files**: snake_case (e.g., `database_handler.py`)
- **Classes**: PascalCase (e.g., `DatabaseHandler`, `IntegrationBase`)
- **Functions/Methods**: snake_case with leading underscore for private (e.g., `_on_message`, `scrape_ads`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `COMMANDS`)

### Async Patterns
- Use `async def` for all I/O operations
- Session management: create in `_on_ready`, close on shutdown
- Random delays between requests: `await asyncio.sleep(random.uniform(min, max))`
- Exponential backoff for retries with max_retries config

### Error Handling
- Central logger: `pyhabot_logger` with DEBUG level
- Argparse errors raise ValueError, returned as chat messages
- Network errors: retry with exponential backoff
- Log warnings/errors, don't crash main loop

### Database Patterns
- TinyDB doc_id as primary key
- Watch: id, url, last_checked, notifyon, webhook
- Advertisement: id (from site), title, url, price, prev_prices[], active flag
- Use `DatabaseHandler` methods, not direct TinyDB access

### Scraping Guidelines
- Randomized User-Agent from config list
- Respect robots.txt (checked at startup)
- Configurable delays between requests (jitter applied)
- Parse with BeautifulSoup: select by CSS classes
- Handle missing fields gracefully (default None/0)

## Important Notes

### Known Limitations
- **Scraper is brittle**: Tightly coupled to HardverApró HTML structure (class names like `uad-list`). Will break if site changes.
- **No rate limiting**: Only basic delays; no per-domain throttling
- **TinyDB concurrency**: Single JSON file, no locking—avoid concurrent writes
- **Webhook failures**: No retry logic, only logged
- **Mixed language**: Commands and help mostly in Hungarian

### Testing Gaps
- No unit tests for parsers (`convert_date`, `convert_price`, `scrape_ads`)
- No CI pipeline
- No type checking configuration (consider adding mypy)
- Terminal integration has limited testing coverage

### When Modifying Code
1. **Scraper changes**: Test against live HardverApró pages; site structure may vary
2. **Integration changes**: Test message formatting per platform (Markdown escaping differs)
3. **Database changes**: Ensure backward compatibility with existing JSON files
4. **Config changes**: Update defaults in `config_handler.py` and provide migration path
5. **Commands**: Update help text in Hungarian and consider English localization

### Environment Variables
- `INTEGRATION`: discord | terminal (required)
- `DISCORD_TOKEN`: Auth token (required for Discord integration)
- `PERSISTENT_DATA_PATH`: Data directory (default: `./persistent_data`)

## Suggested Improvements (Tech Debt)
- Add unit tests with HTML fixtures
- Centralize message formatting with proper Markdown escaping
- Implement crawl-delay adherence from robots.txt
- Replace TinyDB with SQLite for better concurrency and indexing
- Add graceful shutdown hook for aiohttp session cleanup
- Webhook retry/backoff logic
- English localization or i18n framework
- Type hints everywhere + mypy in CI

## Command Reference (Quick)
- `!help` - Show commands
- `!add <url>` - Add watch
- `!remove <id>` - Remove watch
- `!list` - List watches
- `!notifyon <id>` - Enable notifications for watch
- `!rescrape [id]` - Force re-scrape
- `!setwebhook <id> <url>` - Set webhook for watch
- `!setpricealert <adid>` - Enable price alerts for ad
