# PYHABOT Architecture

Updated: 2025-10-30

## Purpose
PYHABOT is a small async bot that watches HardverApró search result pages and notifies users about new ads and price changes. It supports multiple chat integrations (Discord, Telegram, and a simple terminal mode), persists watches and ads in a TinyDB JSON store, and scrapes pages with aiohttp + BeautifulSoup.

## High-level flow
1. An integration (Discord/Telegram/Terminal) receives a message.
2. Pyhabot parses it as a command (prefix default `!`) using `CommandHandler`.
3. Commands update config or the watch list in TinyDB, or return information to the user.
4. A background task runs forever, checking which watches are due, scraping ads with jittered intervals and randomized User-Agent.
5. New ads are sent as notifications; existing ads update price history and can trigger price-change alerts.

```
[User] -> [Integration] -> (MessageBase) -> [Pyhabot._on_message]
                                    |-> [CommandHandler] -> [ConfigHandler / DatabaseHandler]

[Pyhabot.run_forever] -> [scraper.scrape_ads] -> [DatabaseHandler]
                    -> [new ads] -> [Integration.send_message_to_channel]
                    -> [price change] -> [Integration / Webhook]
```

## Modules and responsibilities
- run.py
  - Bootstraps from environment variable `INTEGRATION` (discord | telegram | terminal)
  - Loads token from env, instantiates selected Integration and Pyhabot, and starts the integration client
- pyhabot/pyhabot.py
  - Orchestrator. Wires config, DB, commands, and integration
  - Lifecycle hooks: `_on_ready`, `_on_message`, graceful aiohttp session management
  - Background loop (`run_forever`) with retry/backoff and timing jitter
  - Business actions: `handle_new_ads`, `_send_notification`, `_send_price_change_alert`
- pyhabot/command_handler.py
  - Declarative command registry `COMMANDS`
  - Thin argparse-based dispatcher with custom error handling
  - Allows dynamic callback registration from `Pyhabot`
- pyhabot/config_handler.py
  - JSON-backed config with defaults and setters that persist immediately
  - Tunables: command prefix, refresh interval, request delays, list of user agents, retry policy
- pyhabot/database_handler.py
  - TinyDB-backed persistence for watches and advertisements
  - Watch CRUD, next-check calculation, advertisement insert/update/inactive, price history, flags
- pyhabot/scraper.py
  - Async scraping of HardverApró list pages (uad-list) via aiohttp session
  - Parsing helpers: `get_url_params`, `convert_date`, `convert_price`
- pyhabot/integrations/
  - integration_base.py: Abstract contracts for messages and integrations
  - discord.py: Discord client implementation (sends messages, handles events)
  - telegram.py: Telegram client (telegrampy)
  - terminal.py: Simple REPL for local testing

## Key data structures
- Watch (TinyDB watchlist table)
  - id: int (doc_id)
  - url: str
  - last_checked: float (epoch seconds)
  - notifyon: { channel_id: int|str, integration: str } | None
  - webhook: str | None
- Advertisement (TinyDB advertisements table)
  - id: int (source ad id; used as doc_id)
  - title, url, price, city, date, pinned
  - seller_name, seller_url, seller_rates, image
  - watch_id: int
  - active: bool
  - prev_prices: list[int]
  - price_alert: bool

## External dependencies
- discord.py 2.5.0 / telegrampy (from git) for chat clients
- aiohttp for HTTP
- beautifulsoup4 for HTML parsing
- tinydb for simple JSON persistence
- python-dotenv for local env loading

## Control flow details
- Startup
  - run.py selects integration and constructs Pyhabot
  - Pyhabot registers command callbacks and integration event handlers
  - Integration starts its own event loop client; on_ready triggers `_on_ready` which creates `aiohttp.ClientSession` and starts the background task
- Commands
  - Messages are parsed by `CommandHandler.handle` if they start with `prefix` (default `!`). The selected command callback runs in Pyhabot instance
- Scheduling
  - `run_forever` computes a jittered interval around `refresh_interval` and checks due watches (`DatabaseHandler.check_needed_for_watches`)
  - Between multiple watches, it adds a random delay between `request_delay_min` and `request_delay_max`
  - Exponential backoff on unexpected errors up to `max_retries`
- Scraping and persistence
  - `scrape_ads(url, session, user_agent)` returns parsed ads
  - For each scraped ad:
    - `add_advertisement` inserts new with `prev_prices=[]` else `update_advertisement` toggles `active=True`, appends last price to `prev_prices` when price changed, and updates `price`
  - Ads not present anymore are marked inactive

## Error handling and logging
- Central logger `pyhabot_logger`, console handler at DEBUG by default (limited to ERROR in terminal mode)
- Argparse errors raise ValueError, which are sent back as chat messages
- Network and loop-level exceptions retry with backoff; exceeded retries skip the cycle

## Potential weak spots / tech debt
- Scraper is tightly coupled to specific page structure (class names). Breaks if site changes; no unit tests for parser
- No rate limiting per domain beyond basic delays; robots.txt is read but not enforced per-path or crawl-delay
- Discord/Telegram message formatting inconsistencies; Markdown escaping can break messages
- TinyDB as single JSON file has concurrency risks and no indexing; ad id collisions rely on remote stability
- Some commands lack input validation (e.g., URL format) and permission checks
- Webhook posting has no retry/backoff; failures are silent except for log
- Session lifecycle could leak if integration shuts down unexpectedly
- A few i18n/mixed-language strings; command help only in Hungarian
- Missing tests and CI; no type checking config. Several minor bugs fixed in this commit previously existed

## Suggested improvements
- Add unit tests for `convert_date`, `convert_price`, and `scrape_ads` with sample HTML fixtures
- Centralize message formatting with proper Markdown escaping per integration
- Add per-watch cooldown and crawl-delay adherence; respect robots.txt crawl-delay if present
- Implement structured logging and optional Sentry
- Add graceful shutdown hook to close aiohttp session
- Optional: replace TinyDB with SQLite + indexes for scale; or keep TinyDB and add simple migrations
- Add retry/backoff for webhooks; handle non-2xx responses
- Provide English help or localization toggles; document all commands
- Pin telegrampy git commit in requirements (already pinned) and consider vendoring if unstable

## Command surface (summary)
- help, settings, setprefix <str>, setinterval <int>
- add <url>, remove <watchid>, list, info <watchid>, seturl <watchid> <url>
- notifyon <watchid>, setwebhook <watchid> <url>, unsetwebhook <watchid>
- rescrape [watchid], listads <watchid>, adinfo <adid>
- setpricealert <adid>, unsetpricealert <adid>

## Data flow diagram (ASCII)
```
+------------------+       command        +--------------------+
| User (Discord/   |  ----------------->  | Integration (SDKs) |
| Telegram/Terminal|                      +---------+----------+
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

Background task:
Pyhabot.run_forever -> scrape_ads(aiohttp) -> DatabaseHandler add/update -> notify via Integration / webhook
```
