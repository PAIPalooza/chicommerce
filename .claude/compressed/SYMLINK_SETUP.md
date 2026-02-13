# .claude Directory Symlink Setup

## What Gets Shared

Symlinked `.claude/` shares:
- **Skills**: Campaign workflows, command docs
- **Slash Commands**: `/campaign-*` operations
- **Config Files**: Server templates, settings

## Setup Instructions

### New Projects

**Option 1: Full Symlink**
```bash
cd /path/to/project
rm -rf .claude
ln -s /Users/aideveloper/core/.claude .claude

# Verify
ls -la .claude
claude /campaign-stats
```

**Option 2: Partial Symlink**
```bash
cd /path/to/project
mkdir -p .claude
ln -s /core/.claude/skills .claude/skills
ln -s /core/.claude/commands .claude/commands
cp /core/.claude/mcp.json.example .claude/mcp.json
```

### Existing Projects
```bash
cd /path/to/project
mv .claude .claude.backup
ln -s /Users/aideveloper/core/.claude .claude
cp .claude.backup/mcp.json .claude/mcp.json.local
```

## Benefits
- Single source of truth
- Consistent practices
- Automatic updates
- Team collaboration

## Update Workflow
1. Change in core repo
2. Commit and push
3. All symlinked projects auto-update

## What NOT to Symlink
❌ `.env`
❌ `node_modules/`
❌ `dist/`
❌ `.git/`
❌ Project-specific configs

## Troubleshooting
- Verify symlink: `ls -la .claude`
- Check command access: `ls .claude/commands/campaign-*.md`
- Always edit in core repo

## Best Practices
### DO
✅ Change only in `core/.claude/`
✅ Commit regularly
✅ Test commands
✅ Document changes

### DON'T
❌ Edit through symlinks
❌ Duplicate shared files
❌ Break symlinks

## Git Configuration
```bash
# Core repo .gitignore
# (keep .claude/)

# Other projects .gitignore
.claude/
# Optional: keep local configs
!.claude/mcp.json.local
```

**Last Updated**: January 5, 2026
**Maintained By**: Engineering Team