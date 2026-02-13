# Git Hooks - Install & Enforcement

## Quick Install
```bash
bash .ainative/hooks/install-hooks.sh
# Alt: bash .claude/hooks/install-hooks.sh
```

## Installed Hooks

### Pre-commit: Blocks
- Root .md (except README/CLAUDE)
- Root/backend .sh scripts
- src/backend .md files

### Commit-msg: Blocks
- AI tool mentions
- AI generation claims
- Third-party attribution

### Allows
- AINative team references
- AINative platform mentions

## Testing
```bash
# Block file placement
touch test.md
git add test.md
git commit -m "test"  # ❌ BLOCKED

# Block AI mentions
git commit -m "Generated with Claude"  # ❌ BLOCKED
```

## Manual Install
```bash
cp .ainative/hooks/pre-commit .git/hooks/
cp .ainative/hooks/commit-msg .git/hooks/
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
```

## Docs
- `.ainative/CRITICAL_FILE_PLACEMENT_RULES.md`
- `.ainative/git-rules.md`