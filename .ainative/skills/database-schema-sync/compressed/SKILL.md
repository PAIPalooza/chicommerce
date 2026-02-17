# Database Schema Management

## SCHEMA SYNC SCRIPT RULES

* ✅ USE: `scripts/sync-production-schema.py` for deployments
* ✅ Idempotent, transparent, safe
* ❌ AVOID: Direct Alembic migrations
* ⚠️ Keep Alembic files for docs

## Workflow

### 1. Dry Run
```bash
python scripts/sync-production-schema.py --dry-run
```

### 2. Apply to Production
```bash
export DATABASE_URL="postgresql://..."
python scripts/sync-production-schema.py --apply
```

### 3. Verify
```bash
psql "$DATABASE_URL" -c "\dt"
```

## Key Locations
* Sync Script: `/Users/aideveloper/core/scripts/sync-production-schema.py`
* Docs: `/Users/aideveloper/core/docs/deployment/SCHEMA_SYNC_GUIDE.md`

## Update Schema Process

### Adding Tables
1. Define models in `src/backend/app/models/`
2. Update sync script
3. Test with `--dry-run`
4. Apply to environments

### Adding Columns
1. Update model
2. Add column check in sync script
3. Use IF NOT EXISTS
4. Test with `--dry-run`

## Safety Checks
* Exists checks before creating
* Transaction safety
* Dry-run mode
* Color-coded output

## CI/CD Integration
```yaml
release: python scripts/sync-production-schema.py --apply
```

## ENFORCEMENT
* ❌ NO manual SQL in production
* ✅ ALWAYS use sync script
* ✅ ALWAYS dry-run first
* ✅ Verify in dev/staging

## VIOLATION CONSEQUENCES
* Schema drift
* Deployment failures
* Potential data loss
* Production downtime

**USE SCHEMA SYNC SCRIPT FOR ALL DATABASE CHANGES.**

## References
* `references/sync-vs-alembic.md`
* `references/workflow-examples.md`
* Validate: `scripts/verify-sync-script.sh`