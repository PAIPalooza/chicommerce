# AI Attribution Enforcement

## Forbidden Terms

### Primary Terms
* "Claude"
* "Anthropic"
* "claude.com"
* "Claude Code/Desktop/AI/Engineer"

### Forbidden Phrases
* "Generated/Powered/Built/Made with Claude"
* "Co-Authored-By: Claude"
* "AI-generated/assisted/powered"

### Forbidden Patterns
* Emoji + "Generated/Powered/Made with"
* Links to claude.com/anthropic.com
* AI tool references

## Correct Examples

### Commit Examples
**❌ INCORRECT:**
```
Feature implementation

🤖 Generated with Claude Code
Co-Authored-By: Claude
```

**✅ CORRECT:**
```
Feature implementation
```

## Git Hooks: Enforcement

```bash
#!/bin/bash
COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

if echo "$COMMIT_MSG" | grep -iE "(claude|anthropic|AI-generated|Generated with)" > /dev/null; then
    echo "❌ ERROR: Forbidden AI attribution"
    exit 1
fi
```

## Violation Detection

```bash
# Check commits
git log -5 --pretty=format:"%s%n%b" | grep -iE "(claude|anthropic|AI-generated)"

# Fix attributed commits
git rebase -i HEAD~5
```

## Why This Matters
1. Professional Appearance
2. Ownership Clarity
3. Client Expectations
4. Brand Consistency
5. Legal Protection

## ZERO-TOLERANCE RULE