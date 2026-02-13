# File Placement Rules

## ZERO TOLERANCE FILE PLACEMENT

### STRICT RULES

* ❌ **FORBIDDEN:** .md files in root dirs (except README.md, CLAUDE.md)
* ❌ **FORBIDDEN:** .sh scripts in backend (except start.sh)

### REQUIRED LOCATIONS

## Backend Docs → `/core/docs/`

* **Issues:** `docs/issues/ISSUE_*.md`, `docs/issues/BUG_*.md`
* **Testing:** `docs/testing/*_TEST*.md`
* **Agent Swarm:** `docs/agent-swarm/AGENT_SWARM_*.md`
* **API:** `docs/api/API_*.md`
* **Deployment:** `docs/deployment/DEPLOYMENT_*.md`
* **Backend Features:** `docs/backend/RLHF_*.md`

## Frontend Docs → `/AINative-website/docs/`

* **Features:** `docs/features/`
* **Testing:** `docs/testing/`
* **Deployment:** `docs/deployment/`

## Scripts → `/core/scripts/`

* **Test scripts:** `scripts/test_*.sh`
* **Migration scripts:** `scripts/*_migration.sh`
* **Utility scripts:** `scripts/*.sh`

## ENFORCEMENT WORKFLOW

1. ✅ Check root directory creation
2. ✅ Use docs/ or scripts/ subfolder
3. ✅ Match filename patterns
4. ✅ Create in correct location first

## VIOLATION CONSEQUENCES

* Project clutter
* Wasted reorganization time
* Inconsistent structure
* Reduced doc findability

**ZERO-TOLERANCE: Always use docs/ or scripts/ subfolders.**

## Reference

See `references/directory-mapping.md` for complete mapping.