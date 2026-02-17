# Coverage Requirements

## Backend (pytest)

**Config (pytest.ini/pyproject.toml):**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

**Running:**
```bash
# Module coverage
pytest tests/test_module.py -v --cov=app.module --cov-report=term-missing

# All tests
pytest -v --cov=app --cov-report=term-missing --cov-report=html
```

**Exclusions (.coveragerc):**
```python
[run]
omit =
    */tests/*
    */migrations/*
    */__init__.py
    */config.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    if __name__ == .__main__.:
```

**Thresholds:**
* Min: 80% overall
* Target: 90%+ new code
* Critical paths: 100%

## Frontend (Jest/npm)

**Config (package.json):**
```json
{
  "jest": {
    "collectCoverageFrom": [
      "src/**/*.{js,jsx,ts,tsx}",
      "!src/**/*.d.ts",
      "!src/index.tsx"
    ],
    "coverageThresholds": {
      "global": {
        "statements": 80,
        "branches": 80,
        "functions": 80,
        "lines": 80
      }
    }
  }
}
```

**Running:**
```bash
# Coverage
npm test -- --coverage
npm test -- --coverage --watch
```

**Thresholds:**
* Statements: 80%+
* Branches: 80%+
* Functions: 80%+
* Lines: 80%+

## Coverage Report

```
Name                  Stmts   Miss  Cover   Missing
---------------------------------------------------
app/api/endpoints.py    250     25    90%   45-47, 89-92
app/services/user.py    180     36    80%   125-135, 201-205
app/models/user.py      120      0   100%
---------------------------------------------------
TOTAL                   550     61    89%
```

**Focus:**
* Cover missing lines
* 100% critical code
* Test branches
* Meaningful tests