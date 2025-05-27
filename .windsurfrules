# ChiCommerce Coding Standards

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Code Style Guidelines](#code-style-guidelines)
4. [API Design](#api-design)
5. [Database Guidelines](#database-guidelines)
6. [Testing Strategy](#testing-strategy)
7. [Security Guidelines](#security-guidelines)
8. [Documentation](#documentation)
9. [Git Workflow](#git-workflow)
10. [CI/CD](#cicd)

## Introduction

This document outlines the coding standards and best practices for the ChiCommerce project, an open-source eCommerce API for customized products. These standards extend and specialize the global Semantic Seed Coding Standards (SSCS) for our specific domain.

## Project Structure

```
chicommerce/
├── alembic/                  # Database migrations
├── app/
│   ├── api/                  # API routes
│   │   ├── v1/               # API version 1
│   │   │   ├── endpoints/     # Route handlers
│   │   │   ├── dependencies/  # FastAPI dependencies
│   │   │   └── api.py        # API router setup
│   │   └── deps.py           # Common dependencies
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Application configuration
│   │   └── security.py       # Security utilities
│   ├── crud/                 # Database operations
│   ├── db/                   # Database connection
│   │   └── session.py        # Database session management
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic models
│   ├── services/             # Business logic
│   └── utils/                # Utility functions
├── tests/                    # Test files
│   ├── api/                  # API tests
│   ├── conftest.py           # Test fixtures
│   └── unit/                 # Unit tests
├── .env.example              # Example environment variables
├── .gitignore
├── alembic.ini               # Alembic configuration
├── main.py                   # Application entry point
├── pyproject.toml            # Project metadata and dependencies
└── README.md
```

## Code Style Guidelines

1. **Python Version**: Python 3.11+
2. **Formatting**:
   - Follow PEP 8
   - Line length: 100 characters
   - Use Black for code formatting
   - Use isort for import sorting
3. **Type Hints**:
   - Use Python type hints for all function signatures
   - Use Pydantic models for data validation
4. **Naming Conventions**:
   - Variables and functions: `snake_case`
   - Classes: `PascalCase`
   - Constants: `UPPER_SNAKE_CASE`
   - Private members: `_leading_underscore`

## API Design

1. **RESTful Principles**:
   - Use HTTP methods appropriately (GET, POST, PUT, DELETE)
   - Use plural nouns for resources (e.g., `/products`)
   - Use hyphens in URLs, underscores in query parameters
   - Version your API (e.g., `/api/v1/products`)

2. **Response Format**:
   ```json
   {
     "data": {},
     "meta": {},
     "errors": []
   }
   ```

3. **Status Codes**:
   - 200: Successful GET/PUT/PATCH
   - 201: Successful POST
   - 204: Successful DELETE
   - 400: Bad Request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not Found
   - 422: Validation Error
   - 500: Internal Server Error

## Database Guidelines

1. **Migrations**:
   - Use Alembic for database migrations
   - Write idempotent migration scripts
   - Include rollback logic in migrations

2. **SQLAlchemy**:
   - Use SQLAlchemy 2.0+ style
   - Define models in `app/models/`
   - Use `async` for database operations
   - Keep business logic out of models

3. **Indexing**:
   - Add indexes for frequently queried columns
   - Consider composite indexes for common query patterns

## Testing Strategy

1. **Test Types**:
   - Unit tests: Test individual functions/classes
   - Integration tests: Test API endpoints
   - E2E tests: Test complete user flows

2. **Test Structure**:
   - Follow Arrange-Act-Assert pattern
   - Use pytest fixtures for test data
   - Mock external services

3. **Code Coverage**:
   - Aim for 80%+ test coverage
   - Include both happy and error paths

## Security Guidelines

1. **Authentication**:
   - Use JWT for API authentication
   - Implement rate limiting
   - Use secure password hashing (bcrypt)

2. **Input Validation**:
   - Validate all user inputs
   - Use Pydantic models for request/response validation
   - Sanitize inputs to prevent XSS/SQL injection

3. **Secrets Management**:
   - Never commit secrets to version control
   - Use environment variables for configuration
   - Use `.env` file for local development

## Documentation

1. **API Documentation**:
   - Use OpenAPI (FastAPI's automatic docs)
   - Document all endpoints, parameters, and responses
   - Include example requests/responses

2. **Code Documentation**:
   - Use Google-style docstrings
   - Document public functions and classes
   - Include type hints in docstrings

3. **Project Documentation**:
   - Keep README.md up to date
   - Document setup and deployment procedures
   - Include architecture decisions (ADRs)

## Git Workflow

1. **Branch Naming**:
   - `feature/` - New features
   - `bugfix/` - Bug fixes
   - `hotfix/` - Critical production fixes
   - `chore/` - Maintenance tasks

2. **Commit Messages**:
   - Use conventional commits
   - Format: `type(scope): description`
   - Types: feat, fix, docs, style, refactor, test, chore

3. **Pull Requests**:
   - Link PRs to issues
   - Include clear descriptions
   - Request code reviews
   - All tests must pass before merging

## CI/CD

1. **Continuous Integration**:
   - Run tests on every push
   - Check code style and type hints
   - Run security scans

2. **Continuous Deployment**:
   - Deploy to staging on merge to main
   - Manual approval for production
   - Use semantic versioning for releases

3. **Environment Variables**:
   - Document all required environment variables
   - Provide default values where possible
   - Use different `.env` files for different environments

## Additional Guidelines

1. **Error Handling**:
   - Use custom exceptions
   - Provide meaningful error messages
   - Log errors with appropriate context

2. **Logging**:
   - Use structured logging
   - Include request IDs for tracing
   - Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)

3. **Performance**:
   - Use async/await for I/O-bound operations
   - Implement caching where appropriate
   - Optimize database queries

4. **Dependencies**:
   - Pin all dependencies
   - Regularly update dependencies
   - Audit for security vulnerabilities

## Code Review Guidelines

1. **Before Submitting**:
   - Self-review your code
   - Ensure tests pass
   - Update documentation if needed

2. **Reviewing Code**:
   - Check for security issues
   - Verify error handling
   - Ensure code follows standards
   - Look for performance optimizations

3. **After Review**:
   - Address all comments
   - Update documentation if needed
   - Squash commits if necessary

## Local Development Setup

1. **Prerequisites**:
   - Python 3.11+
   - PostgreSQL 13+
   - Redis (for caching and sessions)
   - Docker (optional)

2. **Setup**:
   ```bash
   # Clone the repository
   git clone https://github.com/your-org/chicommerce.git
   cd chicommerce
   
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up pre-commit hooks
   pre-commit install
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run database migrations
   alembic upgrade head
   
   # Start the development server
   uvicorn app.main:app --reload
   ```

## Contributing

1. Follow the [GitHub Flow](https://guides.github.com/introduction/flow/)
2. Write clear commit messages
3. Keep PRs focused and small
4. Request reviews from team members
5. Address all review comments before merging

## License

[Specify your license here]
