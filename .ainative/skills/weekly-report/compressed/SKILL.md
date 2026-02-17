# Weekly Report Generation

## Report Structure: Required Sections
1. **Executive Summary**
2. **Developer Velocity**
3. **Major Features**
4. **Critical Bug Fixes**
5. **Security Improvements**
6. **Infrastructure & DevOps**
7. **Frontend Improvements**
8. **Work In Progress**
9. **Commit Statistics**
10. **Success Metrics**
11. **Next Week Priorities**

## Data Collection Process

### Step 1: Load User Identities
```bash
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
    GH_USERNAMES=$(cat .claude/user-identities.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(', '.join(['@' + u for u in data['github_usernames']]))
")
    echo "Generating report for: $PRIMARY_NAME"
else
    GIT_EMAILS=$(git config user.email)
    PRIMARY_NAME=$(git config user.name)
    GH_USERNAMES="@$(gh api user --jq .login)"
fi
```

### Step 2: Gather Git Commits
```bash
AUTHOR_FILTER=$(echo "$GIT_EMAILS" | tr '|' '\n' | sed 's/^/--author="/; s/$/"/' | tr '\n' ' ')

git log $AUTHOR_FILTER --since="7 days ago" --pretty=format:"%h %s (%ae)" --no-merges | head -100
git log $AUTHOR_FILTER --since="7 days ago" --format="%ad" --date=short | sort | uniq -c
git log $AUTHOR_FILTER --since="7 days ago" --no-merges --oneline | wc -l
```

### Step 3-5: Issues, PRs, Velocity Calculation
```bash
# Abbreviated scripts for issues, PRs, velocity calculation
THIS_WEEK_COMMITS=$(git log $AUTHOR_FILTER --since="7 days ago" --no-merges --oneline | wc -l | tr -d ' ')
LAST_WEEK_COMMITS=$(git log $AUTHOR_FILTER --since="14 days ago" --until="7 days ago" --no-merges --oneline | wc -l | tr -d ' ')

WEEKLY_VELOCITY_SCORE=$(echo "$THIS_WEEK_COMMITS * 1 + $ISSUES_CLOSED_WEEK * 5 + $PRS_MERGED_WEEK * 8" | bc)

if [ "$WEEKLY_VELOCITY_SCORE" -ge 100 ] && [ "$THIS_WEEK_COMMITS" -ge 46 ]; then
  PRODUCTIVITY_RATING="🔥 Exceptional (top 10%)"
elif [ "$WEEKLY_VELOCITY_SCORE" -ge 60 ] && [ "$THIS_WEEK_COMMITS" -ge 23 ]; then
  PRODUCTIVITY_RATING="⭐ Strong (top 25%)"
elif [ "$WEEKLY_VELOCITY_SCORE" -ge 30 ] && [ "$THIS_WEEK_COMMITS" -ge 11 ]; then
  PRODUCTIVITY_RATING="✅ Good (above median)"
else
  PRODUCTIVITY_RATING="⚠️ Light Week (below median)"
fi
```

## Report Template

### Key Sections
- **Executive Summary**: [X] commits, major accomplishments
- **Developer Velocity**: Metrics, trends, productivity
- **Features/Fixes**: Detailed implementation
- **Metrics**: Commit stats, success tracking
- **Next Priorities**: Actionable focus areas

## File Naming
`docs/reports/WEEKLY_REPORT_YYYY-MM-DD_username.md`

## Quality Checklist
- [ ] Commits analyzed
- [ ] GitHub issues linked
- [ ] Commit hashes included
- [ ] Impact levels assigned
- [ ] Statistics accurate
- [ ] Priorities actionable

## Commit Categorization
| Prefix | Category |
|--------|----------|
| feat   | Features |
| fix    | Bug Fixes|
| sec    | Security |
| test   | Tests    |
| deploy | DevOps   |

## Impact Assessment
- **CRITICAL**: Core functionality
- **HIGH**: Major features
- **MEDIUM**: Enhancements
- **LOW**: Minor fixes

## Usage
```bash
/weekly-report
/weekly-report --start 2026-01-01 --end 2026-01-07
/weekly-report --author username
```