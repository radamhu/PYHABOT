# Legacy Cleanup Plan

## Status: Ready for Cleanup (Phase 6)

The legacy `pyhabot/` folder can be safely removed as all functionality has been migrated to the new `src/pyhabot/` structure.

## Files to Remove

### Immediate (after deprecation period):
- `pyhabot/` - Entire legacy folder
  - `pyhabot.py` → Migrated to `src/pyhabot/app.py`
  - `command_handler.py` → Migrated to `src/pyhabot/cli.py`
  - `config_handler.py` → Migrated to `src/pyhabot/config.py`
  - `database_handler.py` → Migrated to `src/pyhabot/adapters/repos/tinydb_repo.py`
  - `scraper.py` → Migrated to `src/pyhabot/adapters/scraping/hardverapro.py`
  - `integrations/` → Migrated to `src/pyhabot/adapters/integrations/`

### Future (after stabilization):
- `run.py` - Remove deprecated shim
- Update documentation references to old structure

## Verification Checklist

Before removal, verify:
- [ ] All tests pass with new structure
- [ ] CLI commands work correctly
- [ ] Docker image builds and runs
- [ ] No production dependencies on old structure
- [ ] Migration period has elapsed (2-3 months post-refactor)

## Removal Commands

```bash
# Remove legacy folder
rm -rf pyhabot/

# Remove deprecated shim (future)
rm run.py

# Clean up any remaining __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +
```

## Documentation Updates Needed

After removal:
- Update `docs/ARCHITECTURE.md` to remove old structure references
- Update any remaining documentation that mentions old paths
- Clean up coverage.xml source paths

## Timeline

- **Phase 5 Complete**: Documentation and migration ready
- **Phase 6 (2-3 months later)**: Remove legacy code after stabilization
- **Phase 7**: Clean up any remaining references

## Risk Assessment

**Low Risk**: 
- New structure is fully tested and functional
- Migration guide provides clear transition path
- Backward compatibility maintained via run.py shim
- No external dependencies on old structure

**Mitigations**:
- Keep git history for reference
- Tag release before removal
- Maintain migration documentation