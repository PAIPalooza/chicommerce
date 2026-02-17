# AgentFlow Authentication Rules

## Critical Authentication Requirements

### ZERO TOLERANCE: AUTO_LOGIN Configuration

**Production MUST have `AGENTFLOW_AUTO_LOGIN=false`**

### Environment Variables

```bash
AGENTFLOW_AUTO_LOGIN=false                    # CRITICAL: Never true in production
AGENTFLOW_API_URL=https://api.ainative.studio # Required for AINative API auth
```

## AINative API Integration

### Endpoint & Format

- **Endpoint**: `https://api.ainative.studio/v1/public/auth/login`
- **Content-Type**: `application/x-www-form-urlencoded`
- **Fields**: `username` and `password`

### Correct Implementation

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{ainative_api_url}/v1/public/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10.0
    )
```

## Authentication Flow

### 1. AINative API Authentication

```python
response = await client.post(
    f"{ainative_api_url}/v1/public/auth/login",
    data={"username": username, "password": password},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=10.0
)

if response.status_code == 200:
    user = await get_user_by_username(db, username)
    if not user:
        user = User(
            id=uuid4(),
            username=username,
            password=get_password_hash(password),
            is_active=True,
            is_superuser=(username == "admin@ainative.studio")
        )
        db.add(user)
        await db.commit()
    return user
```

### 2. Fallback to Local Authentication

```python
except Exception as e:
    logger.warning(f"AINative API failed: {e}, falling back to local auth")

user = await get_user_by_username(db, username)
if user and verify_password(password, user.password):
    return user
```

## Testing Authentication

### Test AUTO_LOGIN Status

```bash
curl https://agentflow.ainative.studio/api/v1/auto_login
```

**Expected (Production)**:
```json
{
  "detail": {
    "message": "Auto login is disabled",
    "auto_login": false
  }
}
```

## Troubleshooting

### Login Fails Checklist

1. Verify AINative API accessibility
2. Check environment variables
3. Verify endpoint in code
4. Check content-type
5. Confirm field names

## Security Rules

### ✅ DO
1. Set `AGENTFLOW_AUTO_LOGIN=false` in production
2. Use HTTPS for AINative API calls
3. Hash passwords before storing
4. Validate username/password
5. Log authentication attempts
6. Implement rate limiting
7. Use secure session tokens
8. Auto-create users only on successful AINative auth

### ❌ DON'T
1. Never set `AGENTFLOW_AUTO_LOGIN=true` in production
2. Never log passwords
3. Never store passwords in plain text
4. Never skip AINative API authentication
5. Never hard-code credentials

## Code Location

**File**: `src/backend/base/agentflow/services/auth/utils.py`
**Function**: `authenticate_user(username: str, password: str, db: AsyncSession) -> User | None`

## Verification Checklist

- [ ] `AGENTFLOW_AUTO_LOGIN=false` in Railway
- [ ] Auto-login endpoint returns `{"auto_login": false}`
- [ ] Login with AINative credentials returns tokens
- [ ] Correct API endpoint and method
- [ ] Fallback to local auth works