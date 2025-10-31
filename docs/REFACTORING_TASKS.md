# PYHABOT Refactoring Tasks

Updated: 2025-10-30

This document translates the Refactoring Plan into concrete, small, spec-driven tasks. It follows a SPEC → PLAN → TASKS structure to enable iterative delivery and easy tracking in issues/PRs.

References:
- Refactoring plan: `REFACTORING_PLAN.md`
- Current architecture: `docs/ARCHITECTURE.md`

---

## SPEC

Scope
- Modernize the project with a src/ layout, ports & adapters architecture, typed config, centralized logging, robust error handling, improved tests, and CI.
- Keep current features (Discord/Telegram/Terminal integrations, TinyDB persistence, scraping HardverApró). Provide compatibility or clear migration path.

Non-goals (for this iteration)
- Full database migration to SQLite (provide adapter scaffolding, keep TinyDB default).
- Large feature additions beyond refactor (e.g., GUI, web admin).

Constraints
- Python 3.11+.
- Minimal disruption to existing users; `run.py` must continue to work via shim during migration.

Success Metrics
- Installable package with CLI: `pyhabot run` works for all integrations.
- Tests pass in CI (lint, type-check, unit + integration).
- Clear logs and typed config; graceful shutdown; retries with backoff.

---

## PLAN (Phased Delivery)

Phase 1: Packaging, Logger, Config
- Introduce `pyproject.toml` (Poetry), src/ layout, central logger, typed config.

Phase 2: Ports & Adapters
- Extract domain models and ports; adapt TinyDB repo, scraper, and integrations.

Phase 3: Scheduler & CLI
- Harden background runner; expose CLI commands and deprecate `run.py`.

Phase 4: Tests & CI
- Unit tests for parsers/services; integration test for terminal; GitHub Actions CI with lint + mypy + pytest + coverage.

Phase 5: Docs & Cleanup
- Update README and diagrams; remove shims once stable; finalize migration notes.

---

## TASKS (Small, Trackable Chunks)

Legend
- Status: todo | in-progress | done
- ID format: T-###

General Tracking
- Create one GitHub issue per task (or per small group). Label with `refactor`, `phase:X`, `area:<pkg|scraper|integration|ci|tests|docs>`.

### Phase 1 — Packaging, Logger, Config

- T-001 Packaging: Initialize Poetry and pyproject
  - Status: todo
  - Description: Add `pyproject.toml` with project metadata, dependencies, and dev-deps. Keep `requirements.txt` temporarily.
  - Deliverables: `pyproject.toml`, `poetry.lock` (optional), updated `README` install section.
  - Acceptance: `poetry install` and `pip install -e .` succeed locally.

- T-002 Layout: Create src/ structure and base package
  - Status: todo
  - Description: Create `src/pyhabot/__init__.py` and top-level module skeletons (`cli.py`, `app.py`, `config.py`, `logging.py`, `errors.py`).
  - Deliverables: Directory tree and empty modules with docstrings and TODO markers.
  - Acceptance: `python -c "import pyhabot; print(pyhabot.__name__)"` works when installed editable.

- T-003 Logging: Central logger factory
  - Status: todo
  - Description: Implement `pyhabot.logging.get_logger(name)`; support LOG_LEVEL and JSON/text format via env.
  - Acceptance: Sample usage prints expected format; terminal integration defaults to INFO.

- T-004 Config: Typed config from env/.env
  - Status: todo
  - Description: Implement `pyhabot.config.Config` loading env with `python-dotenv`; validate/coerce; helpful errors.
  - Acceptance: Missing required tokens cause clear error; defaults applied for intervals/delays.

- T-005 Shim: Keep run.py compatibility
  - Status: todo
  - Description: Make `run.py` import and call `pyhabot.cli:main`, logging a deprecation warning.
  - Acceptance: `python run.py` still starts the app.

### Phase 2 — Ports & Adapters

- T-010 Domain: Models and ports
  - Status: todo
  - Description: Create `domain/models.py` (Watch, Advertisement) and `domain/ports.py` (ScraperPort, RepoPort, NotifierPort).
  - Acceptance: Types compile; minimal docstrings and type hints present.

- T-011 Domain: Services (use-cases)
  - Status: todo
  - Description: Implement `domain/services.py` with core flows: watch CRUD, ingest scrape results, price change detection, notifications.
  - Acceptance: Unit tests (later) can exercise services with fakes.

- T-012 Adapter: TinyDB repository
  - Status: todo
  - Description: Implement `adapters/repos/tinydb_repo.py` port; map existing JSON schema; preserve doc_id behavior.
  - Acceptance: Read/write round-trips; inactive ads toggled correctly; price history append logic retained.

- T-013 Adapter: Scraper (HardverApró)
  - Status: todo
  - Description: Port current `scraper.py` into `adapters/scraping/hardverapro.py` with async session injection; keep helpers (`convert_date`, `convert_price`).
  - Acceptance: Parses fixture HTML to expected structures; respects robots.txt (checked once at startup).

- T-014 Adapter: Integrations (Discord/Telegram/Terminal)
  - Status: todo
  - Description: Move `pyhabot/integrations` into `adapters/integrations/` with a `base.py` aligning to NotifierPort/Message abstraction; unify formatting.
  - Acceptance: Existing behaviors preserved; Markdown escaping handled per platform.

- T-015 Adapter: Webhook notifier
  - Status: todo
  - Description: Extract webhook posting into `adapters/notifications/webhook.py` with retry/backoff on non-2xx.
  - Acceptance: Retries transient failures; logs errors once exhausted.

### Phase 3 — Scheduler & CLI

- T-020 Scheduler: Runner with jitter/backoff
  - Status: todo
  - Description: Implement `scheduler/runner.py` that plans due watches, applies random delays, and handles transient errors with capped exponential backoff.
  - Acceptance: Clean cancellation on shutdown; metrics/log context include watch_id and url.

- T-021 CLI: Console entrypoint and commands
  - Status: todo
  - Description: Add `cli.py` with `pyhabot` console script; subcommands: `run`, `add-watch`, `list`, `rescrape`, `setprefix`, `notifyon`, `setwebhook`.
  - Acceptance: Commands work locally; `--help` shows accurate usage.

- T-022 Command migration: Argparse registry → CLI
  - Status: todo
  - Description: Map existing `command_handler.py` commands to CLI; keep behavior compatibility; mark deprecated ones if any.
  - Acceptance: Feature parity confirmed by manual checks and tests.

### Phase 4 — Testing & CI

- T-030 Tests: Fixtures for HardverApró
  - Status: todo
  - Description: Add HTML fixture `tests/fixtures/hardverapro_list.html` and any variants for edge cases.
  - Acceptance: Fixture loaded during tests; documented origin/sanitization.

- T-031 Unit tests: Parsing helpers
  - Status: todo
  - Description: Tests for `convert_price`, `convert_date`, and list parsing.
  - Acceptance: Edge cases covered (missing price/date, pinned ads, different locales).

- T-032 Unit tests: Services
  - Status: todo
  - Description: Tests for price change detection, watch scheduling, and insert/update/inactive logic using fakes.
  - Acceptance: Happy path + at least 2 edge cases per use-case.

- T-033 Integration test: Terminal e2e
  - Status: todo
  - Description: Minimal end-to-end run using terminal integration and fixture HTML (mock network) to validate notifications.
  - Acceptance: Test passes consistently, no network calls.

- T-034 CI: GitHub Actions workflow
  - Status: todo
  - Description: Add `.github/workflows/ci.yml` with Python 3.11+ matrix; steps: setup, cache, install (poetry), ruff, mypy, pytest, coverage upload (artifact).
  - Acceptance: CI green on PRs.

- T-035 Linting/Types: Ruff and mypy config
  - Status: todo
  - Description: Add `ruff.toml` and `mypy.ini` (or pyproject sections) with reasonable rules; add type hints in public APIs.
  - Acceptance: Lint/type-check pass locally and in CI.

### Phase 5 — Docs & Cleanup

- T-040 README: Update for new CLI
  - Status: done
  - Description: Quickstart (Poetry + Docker + pip), environment variables, CLI examples.
  - Deliverables: Updated README.md with installation, configuration, and usage sections.
  - Acceptance: New users can run the app following README only.

- T-041 Diagrams: C4/PlantUML
  - Status: done
  - Description: Add Context/Container diagrams in `docs/`; optional sequence diagram for scrape/notify flow.
  - Deliverables: `docs/context-diagram.puml`, `docs/container-diagram.puml`, `docs/sequence-diagram.puml`.
  - Acceptance: Diagrams render and reflect the new architecture.

- T-042 Migration notes and deprecations
  - Status: done
  - Description: Document TinyDB schema compatibility, `run.py` shim, command migration. Provide checklist to remove shims post-stabilization.
  - Deliverables: `docs/MIGRATION.md` with step-by-step migration guidance.
  - Acceptance: Clear doc section with step-by-step migration guidance.

- T-043 Docker: Update entrypoint
  - Status: done
  - Description: Align Dockerfile/entrypoint to use CLI; pass envs; smaller base image if feasible.
  - Deliverables: Updated Dockerfile, .dockerignore, and Docker documentation.
  - Acceptance: Image builds and runs `pyhabot run` reliably.

---

## Dependencies Map (selected)
- T-002 → depends on T-001
- T-011 → depends on T-010
- T-012/T-013/T-014 → depend on T-010
- T-020 → depends on T-011–T-014
- T-021/T-022 → depend on T-011
- T-031/T-032 → depend on T-011–T-014
- T-034 → depends on T-031–T-033 scaffolding

---

## Acceptance Review Checklist (per phase)
- Phase 1: Install works; config loads; logs consistent.
- Phase 2: Services drive adapters behind ports; feature parity maintained.
- Phase 3: CLI replaces command handler; scheduler stable with backoff/jitter.
- Phase 4: CI green; tests deterministic; coverage reported.
- Phase 5: Docs updated; deprecations documented; Docker runs CLI.

---

## Notes
- Keep changes incremental; prefer adapter wrappers over large rewrites.
- Avoid concurrent writes to TinyDB; document this and consider SQLite adapter when concurrency becomes a need.
- For scraping fragility, prioritize adding fixtures before modifying parser logic.
