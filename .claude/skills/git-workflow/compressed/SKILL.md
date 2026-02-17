# Git & PR Workflow Standards

## Core Principles

* **Small PRs:** ≤300 LOC changed
* **Commit often:** Meaningful commits, clear messages
* **Linear history:** Prefer rebase
* **Professional:** No AI attribution

## 🚨 ZERO-TOLERANCE: NO AI ATTRIBUTION 🚨

### ❌ FORBIDDEN

* AI tool names
* "Generated with"
* AI attribution text
* Branding references
* Tool links/emojis

### ✅ CORRECT FORMAT

* Clean, professional messages
* Clear change descriptions
* No external references

## Examples

### ❌ FORBIDDEN COMMIT

```
Add multi-dimension vector support

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### ✅ CORRECT COMMIT

```
Add multi-dimension vector support

- Support for 384-1536 dimensions
- Update validation logic
- Add test coverage
```

## Enforcement

* Zero-tolerance rule
* Verify commits pre-push
* Review PRs for attribution
* Immediate removal if found
* Applies to ALL repositories

## PR Requirements

* Problem/Context
* Solution summary
* Test plan
* Risk/rollback strategy
* Story link + Type + Estimate

## Reference Files

* `references/ai-attribution-enforcement.md`
* `references/pr-templates.md`
* `references/branch-conventions.md`