# ChiCommerce

Open source eCommerce API for customized products.

## Project Overview

ChiCommerce is a robust, scalable backend API service that powers an eCommerce platform specialized in user-driven product customization (e.g., custom-printed apparel, engraved gifts, build-your-own gift boxes). This backend supports product templating, customization options, cart and checkout flows, payment integration, order management, and fulfillment workflows—without requiring user authentication.

## Features

- Product catalog with customizable templates
- Customization engine for assembling/validating visitor inputs
- Cart & checkout flows including customization data
- Order management with status transitions
- Payment processing (Stripe/PayPal integration)
- Admin endpoints for product/template and order management
- Webhooks for real-time notifications

## Tech Stack

- **Backend Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Data Validation**: Pydantic
- **Authentication**: API Key-based
- **Caching**: Redis (optional)
- **Testing**: Pytest with BDD patterns

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis (optional, for caching)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/PAIPalooza/chicommerce.git
   cd chicommerce
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

7. Access the API documentation:
   - Swagger UI: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc

## Development

### Project Structure

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

### Running Tests

```bash
pytest
```

For more verbose output:

```bash
pytest -v
```

For test coverage:

```bash
pytest --cov=app
```

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

Downgrade migrations:

```bash
alembic downgrade -1  # Downgrade one version
```

## API Documentation

The API follows RESTful principles and uses standard HTTP methods. All responses follow a consistent format:

```json
{
  "data": {},
  "meta": {},
  "errors": []
}
```

### Status Codes

- 200: Successful GET/PUT/PATCH
- 201: Successful POST
- 204: Successful DELETE
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature-name`)
5. Open a Pull Request

Please follow the [Semantic Seed Coding Standards](./RULES.md) for all contributions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
