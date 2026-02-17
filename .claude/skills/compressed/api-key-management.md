# API Key Management - Production Testing

## Creating Test API Keys for Production

### CRITICAL: API Keys are Hashed
- Keys stored as SHA256 hashes
- CANNOT retrieve existing keys
- Can ONLY create new ones

### Steps to Create Test API Key

1. Get Database Public URL
```bash
railway run --service "AINative-Core-Production" printenv DATABASE_PUBLIC_URL
```

2. Generate API Key Script
```python
import psycopg2, hashlib, secrets
from datetime import datetime, timedelta

# Generate key
key_value = f"ainative_test_{secrets.token_urlsafe(32)}"
hashed = hashlib.sha256(key_value.encode()).hexdigest()
prefix = key_value[:12]

# Database connection & key insertion
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("SELECT id FROM users WHERE email = 'admin@ainative.studio' LIMIT 1")
user_id = cur.fetchone()[0]

cur.execute("""
    INSERT INTO api_keys (
        user_id, name, hashed_key, prefix,
        is_active, expires_at, created_at, updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
    RETURNING id
""", (
    user_id,
    "Test Production API",
    hashed,
    prefix,
    True,
    datetime.now() + timedelta(days=7)
))

api_key_id = cur.fetchone()[0]
conn.commit()

print(f"✅ Created test API key: {key_value}")
print(f'export AINATIVE_API_KEY="{key_value}"')
```

3. Test Endpoint
```bash
export AINATIVE_API_KEY="ainative_test_..."
curl -X POST "https://api.ainative.studio/v1/managed/chat/completions" \
  -H "X-API-Key: $AINATIVE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "sdxl", "messages": [{"role": "user", "content": "A red cube"}]}'
```

## Authentication Methods

1. X-API-Key Header (Recommended)
```bash
curl -H "X-API-Key: ainative_test_..." https://api.ainative.studio/v1/...
```

2. Bearer Token (JWT)
```bash
curl -H "Authorization: Bearer eyJhbG..." https://api.ainative.studio/v1/...
```

## Common Errors

- "Invalid API key": Key doesn't exist or incorrectly hashed
- "Could not translate host name": Using internal DATABASE_URL
- "Inactive user": User account disabled
- "Insufficient credits": No user credits

## Cleanup Test API Keys
```python
# Delete test API keys older than 7 days
cur.execute("""
    DELETE FROM api_keys
    WHERE name LIKE 'Test%'
    AND created_at < NOW() - INTERVAL '7 days'
""")
```

## Production API Testing Checklist
- [ ] Get DATABASE_PUBLIC_URL
- [ ] Create test API key
- [ ] Verify user credits
- [ ] Set AINATIVE_API_KEY
- [ ] Test authentication
- [ ] Run endpoint tests
- [ ] Clean up test keys

## Quick Reference

| Task | Command |
|------|---------|
| Get DB URL | `railway run --service "AINative-Core-Production" printenv DATABASE_PUBLIC_URL` |
| Create API key | Use Python script |
| Test auth | `curl -H "X-API-Key: ..." https://api.ainative.studio/health` |

**Last Updated:** 2026-01-15