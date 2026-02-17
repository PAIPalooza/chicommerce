# BDD Test Patterns

## Unit Tests

**Given/When/Then Structure:**
```js
describe('UserService', () => {
  it('creates user w/ valid data', () => {
    const userData = { name: 'John', email: 'john@example.com' };
    const user = userService.createUser(userData);
    expect(user.name).to.equal('John');
    expect(user.email).to.equal('john@example.com');
    expect(user.id).to.exist;
  });
});
```

## Integration Tests

**API Endpoint Testing:**
```python
describe('User API', () => {
  it('creates user w/ valid data', async () => {
    const payload = { name: 'Jane', email: 'jane@example.com' };
    const response = await request(app).post('/users').send(payload);
    expect(response.status).to.equal(201);
    expect(response.body.name).to.equal('Jane');
  });

  it('returns 400 for invalid email', async () => {
    const payload = { name: 'Jane', email: 'invalid-email' };
    const response = await request(app).post('/users').send(payload);
    expect(response.status).to.equal(400);
    expect(response.body.error).to.include('email');
  });
});
```

## Functional/API Tests

**End-to-End Workflow:**
```python
def describe_user_registration_workflow():
    def it_completes_registration_flow():
        user_data = {"name": "Test User", "email": "test@example.com", "password": "SecurePass123!"}
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        user_id = response.json()["id"]

        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
```

## Assertion Patterns

**Common Assertions:**
```js
// Core Assertions
expect(actual).to.equal(expected);
expect(actual).to.deep.equal(expectedObject);
expect(value).to.exist;
expect(value).to.be.a('string');

// Collections
expect(array).to.have.length(3);
expect(array).to.include(item);

// Async
await expect(promise).to.eventually.equal(value);
```

## Deterministic Selectors (UI Tests)

```js
// ✅ GOOD - Deterministic selectors
screen.getByTestId('submit-button');
screen.getByRole('button', { name: 'Submit' });
screen.getByLabelText('Email address');
```