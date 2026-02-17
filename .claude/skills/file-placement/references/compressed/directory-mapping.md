# Directory Mapping - Reference

## Backend Documentation Mapping

| Filename Pattern | Location | Examples |
|-----------------|----------|----------|
| `ISSUE_*.md` | `docs/issues/` | `ISSUE_469_MIGRATION.md` |
| `BUG_*.md` | `docs/issues/` | `BUG_392_TEST_ENDPOINT_FIXES.md` |
| `*_TEST*.md` | `docs/testing/` | `COMPREHENSIVE_TEST_SUITE.md` |
| `AGENT_SWARM_*.md` | `docs/agent-swarm/` | `AGENT_SWARM_ARCHITECTURE.md` |
| `API_*.md` | `docs/api/` | `API_DOCUMENTATION.md` |
| `*_IMPLEMENTATION*.md` | `docs/reports/` | `FEATURE_IMPLEMENTATION_SUMMARY.md` |
| `DEPLOYMENT_*.md` | `docs/deployment/` | `DEPLOYMENT_GUIDE.md` |
| `*_QUICK_*.md` | `docs/quick-reference/` | `API_QUICK_REFERENCE.md` |
| `RLHF_*.md` | `docs/backend/` | `RLHF_ARCHITECTURE.md` |
| `CODING_*.md` | `docs/development-guides/` | `CODING_STANDARDS.md` |
| `PRD_*.md` | `docs/planning/` | `PRD_SSG_IMPLEMENTATION.md` |

## Frontend Documentation Mapping

| Filename Pattern | Location | Examples |
|-----------------|----------|----------|
| Feature docs | `AINative-website/docs/features/` | `AI_KIT_INTEGRATION.md` |
| Frontend tests | `AINative-website/docs/testing/` | `COMPONENT_TEST_COVERAGE.md` |
| Frontend issues | `AINative-website/docs/issues/` | `ISSUE_UI_RENDER_BUG.md` |

## Scripts Mapping

| Script Pattern | Location | Examples |
|---------------|----------|----------|
| `test_*.sh` | `scripts/` | `test_api_endpoints.sh` |
| `*_migration.sh` | `scripts/` | `database_migration.sh` |
| `monitor_*.sh` | `scripts/` | `monitor_performance.sh` |

## Special Cases

### Exceptions (Root-Only Files)
* `README.md`
* `CLAUDE.md`
* `src/backend/README.md`
* `AINative-website/README.md`

### Conflict Resolution
Choose MOST SPECIFIC category:
* `BUG_DEPLOYMENT_RAILWAY.md` → `docs/issues/`
* `API_TEST_GUIDE.md` → `docs/testing/`

## Enforcement Checklist

- [ ] .md file?
- [ ] Not in root/backend/frontend root?
- [ ] Identified correct category
- [ ] Created in correct `docs/[category]/`
- [ ] Verified location before commit

## Common Mistakes

* ❌ Creating files in incorrect locations
* ❌ Moving files post-creation
* ❌ Ignoring mapping rules

ZERO-TOLERANCE RULE. NO EXCEPTIONS.