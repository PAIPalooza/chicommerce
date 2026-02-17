# Mandatory TDD/BDD Testing Strategy

## Core Principles
* BDD Style: `describe/it` syntax for tests
* Test-First: Write failing tests before implementation
* Deterministic: Use data-testid, role, label selectors
* Fast & Light: Prefer unit/integration tests

## Example BDD Structure
```js
describe('Calculator', () => {
  it('adds two positive numbers', () => {
    expect(add(5, 7)).to.equal(12);
  });
});
```

## Mandatory Test Execution

### Requirements
1. Actually run test suite with coverage
2. Confirm all tests pass
3. Verify ≥80% coverage
4. Include test execution output

### Backend (Python)
```bash
python3 -m pytest tests/ -v --cov=app --cov-report=term-missing
```

### Frontend (TypeScript)
```bash
npm test -- --coverage
```

### Evidence Requirement
```
## Test Execution Evidence
### Command:
`pytest tests/test_showcase_videos.py -v --cov=app.api`

### Output:
20 passed in 3.42s
Coverage: 87%
```

## Enforcement
* MANDATORY with NO EXCEPTIONS
* Tests run LOCALLY before commit
* Test output in PR descriptions
* Actual coverage percentages required

## Violation Consequences
* Broken code in production
* Undetected bugs
* Loss of test suite confidence

## Reference
* `references/bdd-patterns.md`
* `references/coverage-requirements.md`