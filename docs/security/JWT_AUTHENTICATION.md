# JWT Authentication Guide

## Overview

ZeroCommerce now supports JWT (JSON Web Token) bearer token authentication alongside the legacy API key authentication. This document explains how to authenticate with the API using JWT tokens and the migration path from API keys.

## Authentication Methods

### JWT Bearer Token (Preferred)

JWT bearer token authentication provides:
- **User-level authentication**: Each user has their own token
- **Role-based access control (RBAC)**: Admin vs. User roles
- **Expiration handling**: Tokens automatically expire for security
- **Token refresh**: Support for refreshing expired tokens
- **Standard compliance**: Follows OAuth 2.0 / OpenID Connect patterns

### API Key (Deprecated)

The X-API-Key header authentication is deprecated and will be removed in a future version. It remains supported for backward compatibility during the transition period.

**Deprecation Notice**: When using API key authentication, warning messages will be logged. All integrations should migrate to JWT tokens.

## Using JWT Authentication

### 1. Obtaining a JWT Token

Create a JWT token with the following payload structure:

```json
{
  "sub": "user-identifier",
  "role": "ADMIN",
  "email": "user@example.com",
  "exp": 1234567890
}
```

**Required Fields**:
- `sub` (subject): Unique user identifier
- `role`: User role - either "ADMIN" or "USER"
- `exp` (expiration): Unix timestamp when token expires

**Optional Fields**:
- `email`: User's email address
- `username`: User's username
- Any other user metadata

**Token Signing**:
```python
from jose import jwt
from datetime import datetime, timedelta

payload = {
    "sub": "user123",
    "role": "ADMIN",
    "email": "admin@example.com",
    "exp": datetime.utcnow() + timedelta(hours=8)
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### 2. Making Authenticated Requests

Include the JWT token in the `Authorization` header with the `Bearer` scheme:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     https://api.example.com/api/v1/products/
```

**Python Example**:
```python
import httpx

headers = {
    "Authorization": f"Bearer {jwt_token}"
}

response = httpx.post(
    "https://api.example.com/api/v1/products/",
    json=product_data,
    headers=headers
)
```

**JavaScript Example**:
```javascript
const response = await fetch('https://api.example.com/api/v1/products/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${jwtToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(productData)
});
```

## Role-Based Access Control

### User Roles

ZeroCommerce supports two primary roles:

1. **ADMIN**: Full access to all endpoints, including:
   - Creating, updating, and deleting products
   - Creating and managing templates
   - Accessing sales reports
   - Viewing webhook logs
   - All administrative functions

2. **USER**: Limited access to public endpoints:
   - Reading products and templates
   - Creating cart sessions
   - Placing orders
   - Public API access

### Admin-Only Endpoints

The following endpoints require `ADMIN` role:

- `POST /api/v1/products/` - Create product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product
- `POST /api/v1/templates/` - Create template
- `PUT /api/v1/templates/{id}` - Update template
- `DELETE /api/v1/templates/{id}` - Delete template
- `GET /api/v1/reports/sales` - Sales reports
- `GET /api/v1/webhooklogs` - Webhook logs
- `POST /api/v1/option-sets/` - Create option set
- `PUT /api/v1/option-sets/{id}` - Update option set
- `DELETE /api/v1/option-sets/{id}` - Delete option set

### Public Endpoints

These endpoints do not require authentication:

- `GET /api/v1/products/` - List products
- `GET /api/v1/products/{id}` - Get product
- `GET /api/v1/templates/` - List templates
- `GET /api/v1/templates/{id}` - Get template
- `POST /api/v1/cart/add` - Add to cart
- `POST /api/v1/cart/checkout` - Checkout
- `GET /api/v1/sessions/{key}/state` - Get session state

## Dependency Usage in Endpoints

### For Admin-Only Endpoints

Use `get_admin_user` dependency to ensure admin access:

```python
from typing import Dict
from fastapi import APIRouter, Depends
from app.api import deps

router = APIRouter()

@router.post("/admin-only-endpoint")
async def admin_endpoint(
    current_user: Dict = Depends(deps.get_admin_user)
):
    # Only ADMIN role can access this
    # current_user contains: {"sub": "...", "role": "ADMIN", ...}
    return {"message": "Admin access granted"}
```

### For Authenticated Endpoints (Any Role)

Use `get_current_user` for endpoints that require authentication but accept any role:

```python
@router.get("/user-endpoint")
async def user_endpoint(
    current_user: Dict = Depends(deps.get_current_user)
):
    # Any authenticated user can access this
    user_id = current_user["sub"]
    user_role = current_user["role"]
    return {"user_id": user_id, "role": user_role}
```

### For Optional Authentication

Use `get_optional_user` for endpoints that work with or without authentication:

```python
from typing import Optional

@router.get("/optional-auth-endpoint")
async def optional_endpoint(
    current_user: Optional[Dict] = Depends(deps.get_optional_user)
):
    if current_user:
        # User is authenticated - provide personalized response
        return {"message": f"Hello, {current_user['sub']}"}
    else:
        # User is not authenticated - provide generic response
        return {"message": "Hello, guest"}
```

## Error Handling

### 401 Unauthorized

Returned when:
- No authentication credentials provided
- JWT token is invalid, expired, or malformed
- JWT token missing required `sub` field

```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden

Returned when:
- User is authenticated but lacks required role (e.g., USER trying to access ADMIN endpoint)
- Invalid API key provided

```json
{
  "detail": "Admin access required. Your role does not have sufficient privileges."
}
```

## Backward Compatibility

### Dual Authentication Support

During the transition period, both authentication methods are supported:

```python
# JWT token (preferred)
headers = {"Authorization": "Bearer eyJhbGc..."}

# API key (deprecated - shows warning)
headers = {"X-API-Key": "admin-api-key"}
```

### Priority Order

When both authentication methods are provided:
1. **JWT token is checked first** - If present, it takes precedence
2. **API key is fallback** - Only used if no JWT token provided

```python
# JWT will be used (API key ignored)
headers = {
    "Authorization": "Bearer eyJhbGc...",
    "X-API-Key": "admin-api-key"
}
```

### Deprecation Warnings

API key usage logs warning messages:

```
WARNING: API Key authentication is deprecated.
Please migrate to JWT bearer token authentication.
API Key support will be removed in a future version.
```

## Migration Guide

### Step 1: Generate JWT Tokens

Implement JWT token generation in your authentication service:

```python
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings

def create_access_token(user_id: str, role: str, email: str) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": user_id,
        "role": role.upper(),
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
```

### Step 2: Update Client Code

Replace X-API-Key headers with Authorization: Bearer:

**Before**:
```python
headers = {"X-API-Key": settings.ADMIN_API_KEY}
```

**After**:
```python
token = create_access_token(user_id="admin", role="ADMIN", email="admin@example.com")
headers = {"Authorization": f"Bearer {token}"}
```

### Step 3: Test Dual Authentication

Verify both methods work during transition:

```python
# Test JWT auth
response = client.post("/api/v1/products/", headers={"Authorization": f"Bearer {token}"})
assert response.status_code == 201

# Test API key still works (with deprecation warning)
response = client.post("/api/v1/products/", headers={"X-API-Key": api_key})
assert response.status_code == 201
```

### Step 4: Monitor Deprecation Warnings

Watch application logs for API key usage:

```bash
grep "API Key authentication is deprecated" application.log
```

### Step 5: Remove API Key Usage

Once all clients migrate to JWT, remove API key headers from requests.

## Security Best Practices

### 1. Use Strong Secret Keys

```python
# .env
SECRET_KEY=<long-random-string-256-bits-minimum>
```

Generate secure keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Set Appropriate Token Expiration

```python
# Short-lived access tokens (1-8 hours)
"exp": datetime.utcnow() + timedelta(hours=1)

# Implement refresh token mechanism for longer sessions
```

### 3. Validate All Token Claims

The `verify_jwt_token` function validates:
- Signature using SECRET_KEY
- Expiration timestamp
- Required `sub` field presence
- Algorithm matches HS256

### 4. Use HTTPS in Production

Always use HTTPS to protect tokens in transit:

```python
# Production settings
TLS_ENABLED = True
HTTPS_REDIRECT_ENABLED = True
```

### 5. Implement Token Refresh

For long-running sessions, implement refresh token flow:

```python
# Issue both access and refresh tokens
access_token = create_access_token(user_id, role, email)
refresh_token = create_refresh_token(user_id)

# Client stores refresh token securely
# Uses refresh token to get new access token when expired
```

### 6. Log Authentication Events

Monitor authentication attempts and failures:

```python
logger.warning(f"Failed authentication attempt from {client_ip}")
logger.info(f"User {user_id} authenticated successfully via JWT")
```

## Testing Authentication

### Unit Tests

Test authentication dependencies directly:

```python
import pytest
from fastapi import HTTPException
from app.api import deps

@pytest.mark.asyncio
async def test_valid_jwt_token():
    token = create_test_jwt(user_id="test", role="ADMIN")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user = await deps.get_current_user(credentials=credentials, api_key=None)

    assert user["sub"] == "test"
    assert user["role"] == "ADMIN"

@pytest.mark.asyncio
async def test_admin_role_required():
    user = {"sub": "user123", "role": "USER"}

    with pytest.raises(HTTPException) as exc:
        await deps.get_admin_user(current_user=user)

    assert exc.value.status_code == 403
```

### Integration Tests

Test full request flow:

```python
def test_create_product_with_jwt(client):
    token = create_test_jwt(user_id="admin", role="ADMIN")

    response = client.post(
        "/api/v1/products/",
        json=product_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
```

## Troubleshooting

### "Invalid authentication credentials"

**Cause**: JWT token signature verification failed

**Solutions**:
- Verify SECRET_KEY matches between token creation and validation
- Ensure algorithm is HS256
- Check token hasn't expired
- Validate token format (header.payload.signature)

### "Invalid token: missing user identifier"

**Cause**: JWT payload missing required `sub` field

**Solution**: Ensure token includes `sub` claim:
```python
payload = {"sub": "user123", "role": "ADMIN", ...}
```

### "Admin access required"

**Cause**: User has USER role but endpoint requires ADMIN

**Solution**: Use admin credentials or request admin access

### "Authentication required"

**Cause**: No authentication provided (no JWT token or API key)

**Solution**: Include Authorization header:
```bash
curl -H "Authorization: Bearer <token>" ...
```

## API Reference

### Dependencies

#### `get_current_user(credentials, api_key) -> Dict`

Returns authenticated user information. Supports dual authentication.

**Returns**:
```python
{
    "sub": "user123",
    "role": "ADMIN",
    "email": "user@example.com"
}
```

**Raises**:
- `HTTPException(401)`: Authentication failed or missing
- `HTTPException(403)`: Invalid API key

#### `get_admin_user(current_user) -> Dict`

Ensures user has ADMIN role. Use for admin-only endpoints.

**Raises**:
- `HTTPException(403)`: User does not have ADMIN role

#### `get_optional_user(credentials, api_key) -> Optional[Dict]`

Returns user if authenticated, None otherwise. For optional auth endpoints.

**Returns**: User dict or None

#### `verify_jwt_token(token) -> Dict`

Low-level JWT validation function.

**Raises**:
- `HTTPException(401)`: Invalid token, expired, or malformed

## Additional Resources

- [JWT.io](https://jwt.io/) - JWT debugger and documentation
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - JWT specification
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/) - FastAPI security documentation
- [python-jose](https://python-jose.readthedocs.io/) - JWT library documentation

## Support

For issues or questions about JWT authentication:
- Check application logs for detailed error messages
- Review test files in `tests/unit/test_auth_dependencies.py`
- Consult the migration guide above
- Contact the development team

## Changelog

**Version 1.0** (2026-02-17)
- Initial JWT authentication implementation
- Dual authentication support (JWT + API key)
- Role-based access control (ADMIN/USER)
- Deprecation of API key authentication
- Comprehensive test coverage
- Security documentation
