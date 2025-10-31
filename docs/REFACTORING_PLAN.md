# PYHABOT Refactoring Plan

Updated: 2025-10-30

This plan proposes a pragmatic modernization of PYHABOT to improve structure, maintainability, developer experience, and scalability, while preserving current features.

## Goals and Success Criteria
- Installable package with clear CLI and integrations.
- Consistent async-first I/O, no silent failures, and robust error handling with logs.
- Tests for scraper parsing and core flows; CI green on PRs.
- Clear configuration strategy (.env + typed config).
- Maintain backward compatibility for persistent TinyDB data or provide a migration path.

## Target Structure (mono-repo, src layout)
```
pyproject.toml
README.md
REFACTORING_PLAN.md

src/
  pyhabot/
    __init__.py
    cli.py                 # entrypoints (console_scripts)
    app.py                 # orchestrator (was pyhabot.py)
    config.py              # typed config from env/.env
    logging.py             # global logger setup
    errors.py              # domain and infra exceptions
    domain/
      models.py            # Watch, Advertisement dataclasses / pydantic models
      ports.py             # interfaces (repositories, notifiers, scraper)
      services.py          # use-cases (watch management, notify)
    adapters/
      repos/
        tinydb_repo.py     # TinyDB implementation of ports.Repository
        sqlite_repo.py     # optional future impl
      scraping/
        hardverapro.py     # scraper impl with aiohttp+bs4
      integrations/
        base.py
        discord.py
        telegram.py
        terminal.py
      notifications/
        webhook.py
    scheduler/
      runner.py            # background loop, backoff, jitter
    commands/
      __init__.py
      registry.py          # argparse/click command binding -> services

 tests/
  unit/
    test_convert_price.py
    test_convert_date.py
    test_scraper_list_parse.py
  integration/
    test_end_to_end_terminal.py
  fixtures/
    hardverapro_list.html

 docs/
  ARCHITECTURE.md
  ADRs/
    0001-src-layout.md
    0002-ports-and-adapters.md
```

## Architectural Style and Principles
- Ports & Adapters (Hexagonal): separate domain (use-cases, models) from adapters (scraper, integrations, persistence).
- SOLID, KISS, 12-factor: small modules; inject dependencies via constructors; no global state except the logger factory.
- Layered flow: CLI → Application (services) → Ports → Adapters → External world.
- Event-driven ready: Define domain events (NewAdFound, PriceChanged) for future queue/webhook expansion.

## Packaging and Entry Points
- Switch to `pyproject.toml` (PEP 621). Provide console script:
  - `pyhabot` → `pyhabot.cli:main`
  - Subcommands: `run`, `add-watch`, `list`, `rescrape`.
- Keep `run.py` as thin shim printing deprecation and calling CLI.

## Configuration Management
- Use `python-dotenv` and typed config in `config.py`:
  - INTEGRATION, DISCORD_TOKEN, TELEGRAM_TOKEN
  - PERSISTENT_DATA_PATH, REFRESH_INTERVAL, REQUEST_DELAY_MIN/MAX, MAX_RETRIES
  - USER_AGENTS (comma-separated), LOG_LEVEL
- Validate and coerce types; fail-fast with helpful messages.

## Async Refactor
- Keep aiohttp for HTTP and ensure a single ClientSession lifecycle.
- Ensure all adapters performing I/O are async; services orchestrate via `await`.
- Scheduler runner uses jitter, backoff with caps, and cancellation-aware sleeps.

## Error Handling and Exceptions
- `errors.py` with typed exceptions: ConfigError, ScrapeError, RepoError, IntegrationError, TransientNetworkError, RateLimited.
- Centralized error boundary in CLI and scheduler to log and map to exit codes.
- Retries only on transient categories; no infinite loops.

## Logging
- Central logger factory `get_logger(__name__)` with JSON/text formats via env.
- Correlation IDs for scrape cycles; include watch_id and url in context.
- Reduce noisy logs in terminal integration (INFO) while keeping DEBUG elsewhere.

## Testing Strategy
- Unit tests for parsing helpers and services (happy path + edge cases).
- Integration tests for end-to-end terminal run with fixture HTML.
- Provide deterministic fixtures and fake time/random where needed.

## CI/CD
- GitHub Actions workflow:
  - Python 3.11+ matrix
  - steps: setup-python → cache → install (poetry) → lint (ruff/mypy) → test (pytest -q) → build
- Optional release job on tag to build and publish to PyPI (trusted publisher).

## Dependency Management
- Adopt Poetry with `pyproject.toml`.
- Pin versions with caret/tilde; keep `telegram.py` pinned by commit.
- Dev deps: `pytest`, `pytest-asyncio`, `coverage`, `ruff`, `mypy`, `types-aiohttp`, `types-beautifulsoup4`.

## Performance and Reliability
- Respect robots.txt crawl-delay; configurable rate limiter per host.
- Add exponential backoff with jitter and max cap; budget-based scheduler.
- Profile with `yappi`/`pyinstrument` for scraping hot spots; cache user-agent selection.

## Documentation
- Update README with quickstart (Docker + pip) and CLI usage.
- Add C4/PlantUML diagrams (Context, Container) in docs/.
- Docstrings and type hints across public APIs; `mkdocs` optional.

## Migration Plan
1. Create `pyproject.toml`, adopt Poetry, keep `requirements.txt` temporarily.
2. Introduce `src/` layout and move modules incrementally (keep import shims for compatibility).
3. Extract domain models/ports; adapt current `DatabaseHandler`, `scraper`, and integrations as adapters.
4. Add CLI and deprecate `run.py`.
5. Introduce tests with fixtures; wire CI.
6. Optional: prepare SQLite repo; keep TinyDB default with migration script.

## Risks and Mitigations
- Scraper brittleness → add fixtures and unit tests before refactor; feature flags to toggle parser versions.
- Breaking changes → maintain import shims and config key mapping; semantic version bump.
- CI flakiness → pin deps, use retries for network in tests, mark slow tests.

## Work Packages (Roadmap)
- WP1: Packaging + Logger + Config (1-2 days)
- WP2: Ports & Adapters scaffolding + move scraper/db/integrations (3-5 days)
- WP3: Scheduler + CLI (2-3 days)
- WP4: Tests + Fixtures + CI (2-4 days)
- WP5: Docs + Diagrams + Cleanup (1-2 days)

## Acceptance Checklist
- `pip install -e .` installs CLI `pyhabot`.
- `pyhabot run` starts with selected integration; clean shutdown.
- Tests: >80% coverage for parsing helpers; e2e terminal passes.
- CI green on lint, type-check, and tests.
- README and diagrams reflect new architecture.
