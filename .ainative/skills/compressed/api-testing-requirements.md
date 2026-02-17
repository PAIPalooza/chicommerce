# API Testing Requirements - MANDATORY

## ABSOLUTE RULES

### Rule 1: Test User-Facing API Endpoint

❌ FORBIDDEN:
- Testing provider/service classes directly
- Bypassing HTTP endpoint

✅ REQUIRED:
- Test actual HTTP endpoint
- Use TestClient
- Verify:
  - Authentication
  - Request validation
  - Response formatting
  - Error handling
  - Credit tracking

### Rule 2: File Naming Convention

- `test_*_api.py` → MUST test API endpoints
- `test_*_service.py` → MAY test service layer
- `test_*_provider.py` → MAY test provider layer

### Rule 3: Integration Tests Use Real Endpoints

```python
# ✅ CORRECT
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.post(
    "/api/v1/managed/chat/completions",
    headers=auth_headers,
    json={...}
)
```

### Rule 4: Verify Complete End-to-End Flow

Verify:
- HTTP request → routing → authentication → service → provider
- Credit consumption
- Error responses
- Response format
- Middleware execution

### Rule 5: Honest Reporting

✅ HONEST:
- Specify exact endpoint tested
- Clarify test scope
- Report actual test coverage

## Enforcement Checklist

- [ ] TestClient used
- [ ] Actual endpoint tested
- [ ] Authentication headers
- [ ] HTTP status codes verified
- [ ] Response JSON validated
- [ ] Database changes checked
- [ ] Error cases tested

## Test Pyramid

1. Unit tests (providers, services)
2. Integration tests (API endpoints)
3. E2E tests (full user flow)

## ZERO TOLERANCE RULE

- Rename misleading tests
- Write proper API integration tests
- Accurately report test coverage

**No excuses. Test the API endpoints.**