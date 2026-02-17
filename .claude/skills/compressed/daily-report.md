# Daily Report Generator

## Usage
```bash
/daily-report
```

## Core Functionality
- Analyze today's Git commits
- Review active issues
- Categorize changes
- Generate markdown report in `docs/reports/daily/`

## Data Collection

### Step 1: Load User Identities
```bash
# Load git identities from config
if [ -f .claude/user-identities.json ]; then
    GIT_EMAILS=$(cat .claude/user-identities.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('|'.join(data['git_emails']))
")
    PRIMARY_NAME=$(cat .claude/user-identities.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['primary_name'])
")
else
    # Fallback to current git user
    GIT_EMAILS=$(git config user.email)
    PRIMARY_NAME=$(git config user.name)
fi
```

### Step 2: Git Commits
```bash
# Build author filter for ALL emails
AUTHOR_FILTER=$(echo "$GIT_EMAILS" | tr '|' '\n' | sed 's/^/--author="/; s/$/"/' | tr '\n' ' ')

# Today's commits by your identities
git log $AUTHOR_FILTER --since="today 00:00" --pretty=format:"%h|%H|%ad|%s|%an|%ae" --date=iso --no-merges

# Commit count and files changed
git log $AUTHOR_FILTER --since="today 00:00" --no-merges --oneline | wc -l
git log $AUTHOR_FILTER --since="today 00:00" --name-only --pretty=format: | sort -u
```

### Step 3: GitHub Issues
```bash
# Issues and PRs
gh issue list --assignee="@me" --state all --limit 50 --json number,title,state,updatedAt,labels
gh pr list --author="@me" --state all --limit 20 --json number,title,state,updatedAt
GH_USERNAME=$(gh api user --jq .login)
```

### Step 4: Developer Velocity
```bash
# Commit and productivity calculations
TODAY_COMMITS=$(git log $AUTHOR_FILTER --since="today 00:00" --no-merges --oneline | wc -l | tr -d ' ')
YESTERDAY_COMMITS=$(git log $AUTHOR_FILTER --since="yesterday 00:00" --until="today 00:00" --no-merges --oneline | wc -l | tr -d ' ')
WEEK_COMMITS=$(git log $AUTHOR_FILTER --since="7 days ago" --no-merges --oneline | wc -l | tr -d ' ')
SEVEN_DAY_AVG=$(echo "scale=1; $WEEK_COMMITS / 7" | bc)

ISSUES_CLOSED_TODAY=$(gh issue list --assignee="@me" --state closed --search "closed:$(date +%Y-%m-%d)" --json number --jq 'length')
PRS_MERGED_TODAY=$(gh pr list --author="@me" --state merged --search "merged:$(date +%Y-%m-%d)" --json number --jq 'length')

# Velocity scoring and rating logic
VELOCITY_SCORE=$(echo "$TODAY_COMMITS * 1 + $ISSUES_CLOSED_TODAY * 3 + $PRS_MERGED_TODAY * 5" | bc)
if [ "$VELOCITY_SCORE" -ge 50 ] && [ "$TODAY_COMMITS" -ge 19 ]; then
  PRODUCTIVITY_RATING="🔥 Exceptional (top 10%)"
elif [ "$VELOCITY_SCORE" -ge 30 ] && [ "$TODAY_COMMITS" -ge 15 ]; then
  PRODUCTIVITY_RATING="⭐ Strong (top 25%)"
elif [ "$VELOCITY_SCORE" -ge 15 ] && [ "$TODAY_COMMITS" -ge 3 ]; then
  PRODUCTIVITY_RATING="✅ Good (above median)"
else
  PRODUCTIVITY_RATING="⚠️ Light (below median)"
fi
```

## Report Sections
| Section | Content |
|---------|---------|
| Summary | Quick work overview |
| Developer Velocity | Performance analysis |
| Commits | Detailed changes |
| Issues | Work status |
| Files Modified | Key changes |
| Next Steps | Tomorrow's priorities |

## Output Location
`docs/reports/daily/DAILY_REPORT_YYYY-MM-DD_username.md`

## Commit Categories
| Keywords | Category | Emoji |
|----------|----------|-------|
| feat, add | Features | ✨ |
| fix | Bug Fixes | 🐛 |
| security | Security | 🔒 |
| test | Tests | ✅ |
| deploy | DevOps | 🚀 |
| doc | Docs | 📝 |
| refactor | Refactor | ♻️ |
| perf | Performance | ⚡ |

## Workflow
1. Run `/daily-report`
2. Gather commit data
3. Fetch GitHub activity
4. Categorize changes
5. Calculate statistics
6. Generate markdown
7. Save report

## Quality Checklist
- [ ] All commits included
- [ ] Commits linked with hashes
- [ ] Issues referenced
- [ ] Categories with emojis
- [ ] Time breakdown estimated
- [ ] Priorities defined
- [ ] Correct file location
- [ ] No sensitive data

## Usage Tips
- **Best Time**: End of day (5-6 PM)
- **Frequency**: Daily
- **Purpose**: Track progress, document decisions, identify blockers

Invoke at day's end to generate progress report.