# Scripts Directory

This directory contains utility scripts for managing the ChiCommerce platform.

## ZeroDB PostgreSQL Scripts

### 1. provision_zerodb_postgres.py

Provisions a dedicated PostgreSQL instance on ZeroDB via the AINative API.

**Usage:**
```bash
python scripts/provision_zerodb_postgres.py
```

**What it does:**
- Checks for existing PostgreSQL instance
- Provisions a new instance if none exists
- Retrieves and stores connection details in `.env`
- Tests the database connection
- Displays setup summary

**Prerequisites:**
- `AINATIVE_API_TOKEN` set in `.env`
- `ZERODB_PROJECT_ID` set in `.env`

**Output:**
- Updates `.env` with:
  - `ZERODB_HOST`
  - `ZERODB_PORT`
  - `ZERODB_DATABASE`
  - `ZERODB_USERNAME`
  - `ZERODB_PASSWORD`
  - `ZERODB_URL`

---

### 2. create_zerodb_schema.py

Creates the database schema for orders on the ZeroDB PostgreSQL instance.

**Usage:**
```bash
python scripts/create_zerodb_schema.py
```

**What it does:**
- Creates `orders` table with all necessary columns
- Creates `order_items` table with foreign key to orders
- Creates `payment_events` table for audit trail
- Sets up indexes for performance optimization
- Configures foreign key constraints with CASCADE delete
- Creates triggers for automatic timestamp updates
- Verifies schema integrity

**Prerequisites:**
- `ZERODB_URL` must be set (run `provision_zerodb_postgres.py` first)

**Tables Created:**
1. **orders** - Main order data (23 columns, 8 indexes)
2. **order_items** - Individual items in orders (9 columns, 2 indexes, 1 FK)
3. **payment_events** - Payment webhook events (13 columns, 4 indexes, 1 FK)

---

### 3. test_zerodb_connection.py

Comprehensive test suite for validating the ZeroDB PostgreSQL setup.

**Usage:**
```bash
python scripts/test_zerodb_connection.py
```

**What it does:**
- Tests basic database connectivity
- Verifies all tables exist
- Validates table structure and columns
- Checks index creation
- Verifies foreign key constraints
- Runs CRUD operation tests
- Tests cascade delete functionality
- Executes performance queries

**Test Suite:**
1. Basic Connection Test
2. Schema Existence Test
3. Table Structure Validation
4. Index Verification
5. Foreign Key Constraints Check
6. Sample CRUD Operations
7. Performance Query Tests

**Exit Codes:**
- `0` - All tests passed
- `1` - One or more tests failed

---

## Other Scripts

### check_db.py

Checks the local database connection and displays schema information.

**Usage:**
```bash
python scripts/check_db.py
```

---

### test_cart.py

Tests cart functionality including adding items and retrieving cart state.

**Usage:**
```bash
python scripts/test_cart.py
```

---

### test_option_sets.py

Tests option sets and product customization options.

**Usage:**
```bash
python scripts/test_option_sets.py
```

---

### create_test_data.py

Creates test data for development and testing purposes.

**Usage:**
```bash
python scripts/create_test_data.py
```

---

## Quick Start for ZeroDB Setup

Follow these steps in order to set up ZeroDB PostgreSQL:

1. **Configure credentials** (`.env`):
   ```bash
   AINATIVE_API_TOKEN=your-token
   ZERODB_PROJECT_ID=your-project-id
   ```

2. **Provision the instance**:
   ```bash
   python scripts/provision_zerodb_postgres.py
   ```

3. **Create the schema**:
   ```bash
   python scripts/create_zerodb_schema.py
   ```

4. **Test the setup**:
   ```bash
   python scripts/test_zerodb_connection.py
   ```

5. **Verify** all tests pass (exit code 0)

## Troubleshooting

### "ZERODB_URL not found"
Run `provision_zerodb_postgres.py` first to provision the instance and set up credentials.

### "AINATIVE_API_TOKEN not found"
Add your API token to `.env`:
```bash
AINATIVE_API_TOKEN=your-token-here
```

### "ZERODB_PROJECT_ID not configured"
Add your project ID to `.env`:
```bash
ZERODB_PROJECT_ID=your-project-id-here
```

### Connection Refused
1. Check that the instance is running in the ZeroDB dashboard
2. Verify credentials in `.env`
3. Check firewall rules

### Schema Creation Fails
1. Ensure provisioning completed successfully
2. Verify you have CREATE TABLE permissions
3. Check the database logs

## Best Practices

1. **Always provision first**: Run `provision_zerodb_postgres.py` before schema creation
2. **Test after setup**: Always run `test_zerodb_connection.py` to verify the setup
3. **Keep credentials secure**: Never commit `.env` file with real credentials
4. **Monitor connections**: Use the test script to check active connections
5. **Regular backups**: Enable automatic backups in ZeroDB dashboard

## Documentation

For detailed documentation, see:
- [ZeroDB Setup Guide](/docs/deployment/ZERODB_SETUP.md)

## Support

For issues:
1. Check the documentation
2. Review script output for error messages
3. Verify environment variables are set correctly
4. Contact support if issues persist
