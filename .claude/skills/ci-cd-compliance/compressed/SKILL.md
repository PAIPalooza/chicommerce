```markdown
# CI/CD Compliance

## CI Gates
install → lint → typecheck → unit → integration → (e2e) → package

## Merge Policy
* Green merge only
* Auto-staging deploy
* Prod needs tag/approval

## Failure Handling
1. Explain root cause
2. Include fix
3. Pass all gates

## IDE Integration
* Use code actions
* Unified diffs
* Attach artifacts

📍 See `references/pipeline-requirements.md`
```