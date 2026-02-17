# ZeroDB PostgreSQL Setup Guide

This guide covers the provisioning and configuration of the dedicated ZeroDB PostgreSQL instance for the ChiCommerce platform.

## Overview

ZeroDB provides a managed PostgreSQL database service optimized for high availability, performance, and security. This instance is used to store order-related data including:

- Orders
- Order items
- Payment events

## Prerequisites

Before provisioning a ZeroDB PostgreSQL instance, ensure you have:

1. An active AINative account
2. API credentials configured in your `.env` file:
   - `AINATIVE_API_URL`
   - `AINATIVE_API_TOKEN`
   - `ZERODB_PROJECT_ID`

## Provisioning the PostgreSQL Instance

### Step 1: Configure Project ID

First, obtain your ZeroDB project ID from the AINative dashboard and add it to your `.env` file:

```bash
ZERODB_PROJECT_ID=your-actual-project-id
```

### Step 2: Run the Provisioning Script

Execute the provisioning script to create a new PostgreSQL instance:

```bash
python scripts/provision_zerodb_postgres.py
```

The script will:
1. Check for an existing PostgreSQL instance
2. Provision a new instance if none exists (using the "starter" plan in "us-west-2" region)
3. Retrieve connection details
4. Update your `.env` file with the connection credentials
5. Test the database connection

### Expected Output

```
============================================================
ZERODB POSTGRESQL PROVISIONER
============================================================

Checking for existing PostgreSQL instance...
No existing instance found.

Provisioning PostgreSQL instance...
  Plan: starter
  Region: us-west-2
  Project ID: your-project-id

✓ PostgreSQL instance provisioned successfully!

Updating .env file with ZeroDB connection details...
  Host: your-instance.zerodb.cloud
  Port: 5432
  Database: zerodb_db
  Username: zerodb_user

✓ Environment file updated successfully!

Testing database connection...
✓ Connection successful!
  PostgreSQL version: PostgreSQL 15.4...
  Database: zerodb_db
  User: zerodb_user

============================================================
ZERODB POSTGRESQL INSTANCE PROVISIONED
============================================================
```

### Step 3: Create Database Schema

After provisioning, create the required database schema:

```bash
python scripts/create_zerodb_schema.py
```

This script creates:
- `orders` table with all required columns
- `order_items` table with foreign key to orders
- `payment_events` table for audit trail
- All necessary indexes for performance
- Foreign key constraints
- Triggers for automatic timestamp updates

### Expected Output

```
============================================================
ZERODB SCHEMA CREATOR
============================================================

Creating orders table...
  ✓ orders table created successfully!

Creating order_items table...
  ✓ order_items table created successfully!

Creating payment_events table...
  ✓ payment_events table created successfully!

Verifying schema...
  ✓ orders table exists
    - 23 columns
    - 8 indexes
  ✓ order_items table exists
    - 9 columns
    - 2 indexes
    - 1 foreign key constraints
  ✓ payment_events table exists
    - 13 columns
    - 4 indexes
    - 1 foreign key constraints

Running sample queries...
  ✓ Count orders: 0
  ✓ Count order items: 0
  ✓ Count payment events: 0
  ✓ List indexes on orders: 8 results

✓ Schema creation completed successfully!
```

## Connection Details

After provisioning, the following environment variables will be automatically set in your `.env` file:

```bash
ZERODB_HOST=your-instance.zerodb.cloud
ZERODB_PORT=5432
ZERODB_DATABASE=zerodb_db
ZERODB_USERNAME=zerodb_user
ZERODB_PASSWORD=your-secure-password
ZERODB_URL=postgresql+psycopg2://zerodb_user:password@host:5432/zerodb_db
```

## Database Schema

### Orders Table

Stores order information including payment status, shipping details, and financial data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| cart_id | UUID | Reference to cart |
| user_id | UUID | User ID (nullable for guest checkout) |
| session_id | VARCHAR(255) | Session identifier |
| status | VARCHAR(50) | Order status (created, pending_payment, paid, etc.) |
| payment_provider | VARCHAR(50) | Payment provider (stripe, paypal) |
| payment_intent_id | VARCHAR(255) | Payment intent ID from provider |
| payment_status | VARCHAR(50) | Payment status |
| subtotal | NUMERIC(10,2) | Order subtotal |
| tax | NUMERIC(10,2) | Tax amount |
| shipping_cost | NUMERIC(10,2) | Shipping cost |
| total | NUMERIC(10,2) | Total amount |
| currency | VARCHAR(3) | Currency code (default: USD) |
| shipping_address | JSONB | Shipping address details |
| billing_address | JSONB | Billing address details |
| tracking_url | VARCHAR(500) | Shipment tracking URL |
| customer_email | VARCHAR(255) | Customer email |
| customer_phone | VARCHAR(50) | Customer phone |
| notes | TEXT | Order notes |
| order_metadata | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| paid_at | TIMESTAMP | Payment timestamp |

**Indexes:**
- `idx_orders_cart_id` on `cart_id`
- `idx_orders_user_id` on `user_id`
- `idx_orders_session_id` on `session_id`
- `idx_orders_status` on `status`
- `idx_orders_payment_intent_id` on `payment_intent_id`
- `idx_orders_customer_email` on `customer_email`
- `idx_orders_tracking_url` on `tracking_url`
- `idx_order_status_created` on `(status, created_at)`

### Order Items Table

Stores individual items within an order with customization data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| order_id | UUID | Foreign key to orders |
| product_id | UUID | Product reference |
| product_name | VARCHAR(255) | Product name snapshot |
| quantity | INTEGER | Quantity ordered |
| unit_price | NUMERIC(10,2) | Price per unit |
| total_price | NUMERIC(10,2) | Total price |
| customization_data | JSONB | Product customizations |
| created_at | TIMESTAMP | Creation timestamp |

**Indexes:**
- `idx_order_items_order_id` on `order_id`
- `idx_order_items_product_id` on `product_id`

**Constraints:**
- Foreign key on `order_id` with CASCADE delete
- Check constraint: `quantity > 0`
- Check constraint: `unit_price >= 0`
- Check constraint: `total_price >= 0`

### Payment Events Table

Stores payment webhook events for audit trail and idempotency.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| order_id | UUID | Foreign key to orders |
| event_id | VARCHAR(255) | Unique provider event ID |
| event_type | VARCHAR(100) | Event type |
| provider | VARCHAR(50) | Payment provider |
| payment_intent_id | VARCHAR(255) | Payment intent ID |
| amount | NUMERIC(10,2) | Payment amount |
| currency | VARCHAR(3) | Currency code |
| payload | JSONB | Full event payload |
| processed | BOOLEAN | Processing status |
| processed_at | TIMESTAMP | Processing timestamp |
| processing_error | TEXT | Error message if processing failed |
| created_at | TIMESTAMP | Event creation timestamp |

**Indexes:**
- `idx_payment_events_order_id` on `order_id`
- `idx_payment_events_event_id` on `event_id` (UNIQUE)
- `idx_payment_event_provider` on `(provider, event_type)`
- `idx_payment_event_processed` on `(processed, created_at)`

**Constraints:**
- Foreign key on `order_id` with CASCADE delete
- Check constraint: `provider IN ('stripe', 'paypal')`
- Unique constraint on `event_id` for idempotency

## Using ZeroDB in Your Application

### Connecting to ZeroDB

To use the ZeroDB connection in your application, you can either:

1. **Use the `ZERODB_URL` directly:**

```python
from sqlalchemy import create_engine
from app.core.config import settings

engine = create_engine(
    settings.ZERODB_URL,
    pool_pre_ping=True,
    echo=settings.LOG_LEVEL == "DEBUG"
)
```

2. **Construct the URL from components:**

```python
from app.core.config import settings

url = (
    f"postgresql+psycopg2://{settings.ZERODB_USERNAME}:"
    f"{settings.ZERODB_PASSWORD}@{settings.ZERODB_HOST}:"
    f"{settings.ZERODB_PORT}/{settings.ZERODB_DATABASE}"
)
```

### Creating a Separate Session for ZeroDB

If you want to use ZeroDB alongside your existing database:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create ZeroDB engine
zerodb_engine = create_engine(
    settings.ZERODB_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
ZeroDBSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=zerodb_engine
)

def get_zerodb() -> Generator[Session, None, None]:
    """Dependency for ZeroDB sessions."""
    db = ZeroDBSession()
    try:
        yield db
    finally:
        db.close()
```

## Testing the Connection

You can test the connection at any time using:

```bash
python -c "
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv('ZERODB_URL'), pool_pre_ping=True)
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()'))
    print('Connected!', result.fetchone()[0][:50])
"
```

## Performance Optimization

### Connection Pooling

ZeroDB supports connection pooling. Recommended settings:

```python
engine = create_engine(
    settings.ZERODB_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,        # Number of connections to maintain
    max_overflow=20,     # Additional connections under load
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

### Query Performance

All tables are created with appropriate indexes. Monitor query performance using:

```sql
-- Show slow queries
SELECT * FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Show table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Security Best Practices

1. **Never commit credentials:** The `.env` file is gitignored. Never commit database credentials.

2. **Use environment variables:** Always load credentials from environment variables, not hardcoded values.

3. **Rotate passwords regularly:** Change the database password periodically using the ZeroDB dashboard.

4. **Use SSL/TLS:** ZeroDB connections use SSL/TLS by default for encryption in transit.

5. **Limit access:** Only grant necessary permissions to application users.

## Troubleshooting

### Connection Refused

If you get a connection refused error:

1. Verify the instance is running in the ZeroDB dashboard
2. Check firewall rules
3. Verify the credentials in `.env`

### Schema Creation Fails

If schema creation fails:

1. Ensure the provisioning script completed successfully
2. Check that `ZERODB_URL` is set in `.env`
3. Verify you have CREATE TABLE permissions

### Too Many Connections

If you exceed connection limits:

1. Reduce `pool_size` and `max_overflow`
2. Ensure connections are properly closed
3. Use connection pooling properly
4. Consider upgrading to a higher tier plan

## Maintenance

### Backups

ZeroDB automatically creates daily backups. To create a manual backup:

```bash
# Using the ZeroDB API or dashboard
# Contact support for backup restoration
```

### Monitoring

Monitor your instance using:

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Table statistics
SELECT * FROM pg_stat_user_tables;
```

## Support

For issues with ZeroDB:
- Check the AINative documentation
- Contact support through the dashboard
- Review the provisioning logs

## Next Steps

After setting up ZeroDB:

1. Run your application migrations
2. Test order creation workflows
3. Monitor performance metrics
4. Set up backup verification
5. Configure monitoring alerts

## API Reference

### Provisioning Endpoint

```
POST /v1/public/projects/{project_id}/postgres
```

**Request Body:**
```json
{
  "plan": "starter",
  "region": "us-west-2"
}
```

**Response:**
```json
{
  "host": "your-instance.zerodb.cloud",
  "port": 5432,
  "database": "zerodb_db",
  "username": "zerodb_user",
  "password": "secure-password",
  "status": "active"
}
```

### Available Regions

- `us-east-1` - US East (Virginia)
- `us-west-2` - US West (Oregon)
- `eu-west-1` - EU West (Ireland)
- `ap-southeast-1` - Asia Pacific (Singapore)

### Available Plans

- `starter` - 2 vCPU, 4GB RAM, 20GB storage
- `professional` - 4 vCPU, 8GB RAM, 100GB storage
- `enterprise` - Custom configuration

## Changelog

### 2026-02-17
- Initial provisioning setup
- Created orders, order_items, and payment_events tables
- Added comprehensive indexes and constraints
- Documented connection setup and usage
