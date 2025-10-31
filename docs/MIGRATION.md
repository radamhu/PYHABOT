# PYHABOT Migration Guide

This document helps users migrate from the legacy PYHABOT to the new refactored version with proper packaging, CLI, and improved architecture.

## What Changed

### Architecture
- **New src/ layout**: Code moved to `src/pyhabot/` following Python packaging best practices
- **Ports & Adapters**: Clean separation between domain logic and external dependencies
- **Typed Configuration**: Environment-based config with validation and helpful error messages
- **Centralized Logging**: Structured logging with configurable levels and formats
- **CLI Interface**: New `pyhabot` command with subcommands
- **Better Error Handling**: Graceful degradation with retries and backoff

### Installation
- **Poetry support**: Modern dependency management with `pyproject.toml`
- **Proper packaging**: Installable as `pip install -e .` with console scripts
- **Development tools**: Integrated linting, type checking, and testing

## Migration Steps

### 1. Update Installation

#### Before (Legacy)
```bash
git clone <repo>
cd PYHABOT
pip install -r requirements.txt
python run.py
```

#### After (New)
```bash
git clone <repo>
cd PYHABOT

# Option 1: Poetry (Recommended)
poetry install
poetry shell
pyhabot run

# Option 2: pip
pip install -e .
pyhabot run
```

### 2. Update Configuration

#### Environment Variables
The new version uses the same environment variables but with better validation:

```bash
# Required
INTEGRATION=discord  # or telegram, terminal
DISCORD_TOKEN=your_token  # or TELEGRAM_TOKEN

# Optional (with defaults)
PERSISTENT_DATA_PATH=./persistent_data
LOG_LEVEL=INFO
SCRAPE_INTERVAL=300
REQUEST_DELAY_MIN=1
REQUEST_DELAY_MAX=3
```

#### Configuration Validation
Missing required tokens now show clear error messages:
```
Error: DISCORD_TOKEN is required when INTEGRATION=discord
```

### 3. Update Running Method

#### Before (Legacy)
```bash
python run.py
```

#### After (New)
```bash
# Use the CLI
pyhabot run

# Or specify integration
pyhabot run --integration discord

# Legacy still works (with deprecation warning)
python run.py
```

### 4. Update Docker Deployment

#### Before (Legacy)
```dockerfile
CMD ["python3", "-u", "/app/run.py"]
```

#### After (New)
```dockerfile
# Install as package first
RUN pip install -e .
CMD ["pyhabot", "run"]
```

## Data Compatibility

### TinyDB Schema
The TinyDB JSON schema is **fully compatible** - no migration needed:

- **Watches**: Same structure with `id`, `url`, `last_checked`, `notifyon`, `webhook`
- **Advertisements**: Same structure with `id`, `title`, `url`, `price`, `prev_prices`, `active`

### Data Location
Default data location remains `./persistent_data/` but is now configurable:
```bash
PERSISTENT_DATA_PATH=/custom/path
```

## Command Compatibility

### Chat Commands (Unchanged)
All existing chat commands work exactly the same:
- `!add <url>`
- `!list`
- `!remove <id>`
- `!notifyon <id>`
- etc.

### New CLI Commands (Additional)
New CLI commands provide management outside of chat:
```bash
pyhabot add-watch <url>
pyhabot list
pyhabot rescrape <id>
```

## Deprecation Timeline

### Phase 1: Current (Graceful Migration)
- `run.py` shows deprecation warning
- All legacy features work
- Documentation covers both methods

### Phase 2: Stabilization (After 2-3 months)
- Remove `run.py` shim
- Update all documentation to CLI-only
- Consider legacy chat commands deprecation

### Phase 3: Future (6+ months)
- Potential breaking changes for major improvements
- SQLite adapter option (TinyDB remains default)

## Migration Checklist

### Pre-Migration
- [ ] Backup `persistent_data/` directory
- [ ] Note current configuration values
- [ ] Document any custom modifications

### Migration
- [ ] Update installation method (Poetry or pip)
- [ ] Test with `pyhabot run --integration terminal`
- [ ] Verify all watches work: `!list`
- [ ] Test notifications: `!rescrape <id>`

### Post-Migration
- [ ] Update deployment scripts
- [ ] Update Docker configurations
- [ ] Update monitoring/alerts
- [ ] Remove old `requirements.txt` if using Poetry

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'pyhabot'"
```bash
# Install in development mode
pip install -e .
# Or with Poetry
poetry install
```

#### "DISCORD_TOKEN is required"
Ensure environment variables are set:
```bash
export DISCORD_TOKEN=your_token
# Or create .env file
echo "DISCORD_TOKEN=your_token" > .env
```

#### "pyhabot: command not found"
```bash
# Ensure PATH includes user scripts
export PATH="$HOME/.local/bin:$PATH"
# Or use python -m
python -m pyhabot run
```

### Getting Help

- Check logs: Set `LOG_LEVEL=DEBUG` for detailed output
- Validate config: `pyhabot run --help` shows all options
- Report issues: Include migration step and error details

## Rollback Plan

If you need to rollback to the legacy version:

1. **Restore data**: Copy back `persistent_data/` backup
2. **Install legacy**: `pip install -r requirements.txt` (if available)
3. **Run legacy**: `python run.py`

The data format is compatible, so rollback should be seamless.

## Developer Migration

For developers with custom modifications:

1. **Check imports**: Update to new `src/pyhabot/` paths
2. **Review adapters**: Use new ports & adapters interfaces
3. **Update tests**: Use new fixtures and test structure
4. **Follow patterns**: Use typed config and centralized logging

See `docs/ARCHITECTURE.md` for detailed new architecture information.