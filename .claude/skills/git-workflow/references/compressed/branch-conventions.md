# Branch Naming Conventions

## Patterns

Branches follow:
```
feature/{issue-id}-{slug}
bug/{issue-id}-{slug}
chore/{issue-id}-{slug}
```

Where:
* `{issue-id}` = GitHub/Shortcut issue number
* `{slug}` = 2-4 word hyphen-separated description

## Examples

### Feature Branches
```
feature/123-add-user-auth
feature/456-vector-search-api
feature/789-stripe-integration
```

### Bug Fix Branches
```
bug/111-fix-login-redirect
bug/222-memory-leak-fix
bug/333-race-condition-search
```

### Chore Branches
```
chore/199-upgrade-dependencies
chore/200-refactor-auth-module
chore/201-add-logging
```

## Slug Guidelines

### Rules
1. 2-4 words max
2. Hyphen-separated
3. Lowercase
4. Descriptive & brief
5. No version numbers
6. Action/problem-oriented

### Good/Bad Examples
* ✅ `add-user-auth`
* ✅ `fix-login-redirect`
* ❌ `implement-complex-authentication-system`
* ❌ `update`

## Branch Creation

```bash
# From main
git checkout main
git pull origin main

# Create branches
git checkout -b feature/123-add-user-auth
git checkout -b bug/456-fix-login-redirect
```

## Branch Lifecycle
1. Create from main
2. Commit following TDD
3. Push to remote
4. Create PR
5. Delete after merge

## Avoid
* ❌ Branches without issue numbers
* ❌ Unclear branch names
* ❌ Developing on `main`
* ❌ Reusing branch names