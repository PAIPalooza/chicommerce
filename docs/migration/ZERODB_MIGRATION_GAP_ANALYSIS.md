# ZeroCommerce - ZeroDB Migration Gap Analysis

**Document Version:** 1.0
**Date:** 2026-02-16
**Status:** Draft
**Author:** AINative Dev Team

---

## Executive Summary

This document provides a comprehensive gap analysis for migrating ZeroCommerce from a traditional PostgreSQL + SQLAlchemy architecture to the AINative Studio ZeroDB platform with integrated AINative authentication.

### Migration Scope

1. **Authentication Migration**: Replace custom API key authentication with AINative OAuth
2. **Database Migration**: PostgreSQL → ZeroDB NoSQL Tables
3. **File Storage Migration**: AWS S3 → ZeroDB Files
4. **Event System**: Custom webhooks → ZeroDB Events
5. **Caching**: Redis → ZeroDB Memory (optional)

### Impact Assessment

| Category | Current | Target | Effort | Risk |
|----------|---------|--------|--------|------|
| Authentication | Custom API Key | AINative OAuth | Medium | Low |
| Database | PostgreSQL + SQLAlchemy | ZeroDB NoSQL Tables | High | Medium |
| File Storage | AWS S3 | ZeroDB Files | Low | Low |
| Events | Custom Webhooks | ZeroDB Events | Medium | Low |
| Caching | Redis | ZeroDB Memory | Low | Low |

---

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Target Architecture](#target-architecture)
3. [Authentication Gap Analysis](#authentication-gap-analysis)
4. [Database Gap Analysis](#database-gap-analysis)
5. [API Endpoint Mapping](#api-endpoint-mapping)
6. [Data Model Migration](#data-model-migration)
7. [Code Changes Required](#code-changes-required)
8. [Migration Strategy](#migration-strategy)
9. [Risk Assessment](#risk-assessment)
10. [Recommendations](#recommendations)

---

## 1. Current Architecture Analysis

### 1.1 Technology Stack

**Current Stack:**
- **Framework**: FastAPI
- **Database**: PostgreSQL 13+ with SQLAlchemy 2.0 ORM
- **Authentication**: Custom API Key (X-API-Key header)
- **Caching**: Redis (optional)
- **File Storage**: AWS S3
- **Migrations**: Alembic
- **Testing**: Pytest with 92% coverage

### 1.2 Data Models

**Current Models (SQLAlchemy):**

| Model | Table | Relationships | Key Features |
|-------|-------|---------------|--------------|
| Product | products | → Template (FK) | UUID, versioning, pricing |
| Template | templates | ← Product, → CustomizationZones | UUID, JSONB constraints |
| OptionSet | option_sets | Many-to-Many with Products | JSONB options, pricing |
| CustomizationSession | customization_sessions | → Product, Template | Session keys, JSONB options |
| Order | orders | → OrderItems, PaymentEvents | State machine, pricing |
| OrderItem | order_items | → Order, Product | Line items, customizations |
| PaymentEvent | payment_events | → Order | Stripe/PayPal webhooks |
| WebhookLog | webhook_logs | None | Audit trail, retry logic |

**Total Tables**: 8 core tables + supporting tables

### 1.3 Current API Endpoints

**Endpoint Count**: 35+ endpoints across 9 routers

| Router | Endpoints | Authentication |
|--------|-----------|----------------|
| `/products` | 5 | Public + Admin |
| `/templates` | 5 | Public + Admin |
| `/option-sets` | 5 | Public + Admin |
| `/cart` | 3 | Public |
| `/sessions` | 2 | Public |
| `/webhooks` | 3 | Webhook signatures |
| `/reports` | 1 | Admin only |
| `/webhooklogs` | 1 | Admin only |
| Root | 3 | Public |

### 1.4 Authentication Flow

```
Current Flow:
1. Client sends request with X-API-Key header
2. FastAPI dependency (get_admin_key) validates against settings.ADMIN_API_KEY
3. Request proceeds or returns 401/403

Limitations:
- Single admin API key (no user management)
- No token refresh
- No OAuth support
- No user roles/permissions
- No session management
```

### 1.5 Database Operations

**CRUD Patterns:**
```python
# Current SQLAlchemy pattern
def get_product(db: Session, product_id: UUID) -> Product:
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
```

**Complex Queries:**
- JOIN operations across 3+ tables
- Aggregate functions (SUM, COUNT, AVG)
- Transaction management
- Foreign key constraints
- Unique constraints

---

## 2. Target Architecture

### 2.1 AINative Platform Stack

**Target Stack:**
- **Framework**: FastAPI (retained)
- **Database**: ZeroDB NoSQL Tables
- **Authentication**: AINative OAuth 2.0 + JWT
- **Caching**: ZeroDB Memory
- **File Storage**: ZeroDB Files
- **Vector Search**: ZeroDB Vectors (new capability)
- **Events**: ZeroDB Event Streams
- **Embeddings**: Built-in embedding service

### 2.2 ZeroDB Capabilities

| Feature | Description | Use Case in ZeroCommerce |
|---------|-------------|--------------------------|
| NoSQL Tables | Schema-flexible document store | Product catalog, orders |
| Vectors | Semantic search with embeddings | Product search, recommendations |
| Memory | Agent context storage | User sessions, cart state |
| Events | Pub/sub event streaming | Order events, webhooks |
| Files | Object storage with presigned URLs | Product images, design previews |
| PostgreSQL | Dedicated SQL instances (optional) | Complex analytics, reporting |

### 2.3 AINative Authentication

**OAuth 2.0 Flow:**
```
1. User Registration/Login
   POST /v1/public/auth/register
   POST /v1/public/auth/login-json

2. Token Response
   {
     "access_token": "eyJhbGc...",
     "token_type": "bearer",
     "expires_in": 1800
   }

3. Authenticated Requests
   Authorization: Bearer ACCESS_TOKEN

4. Token Refresh
   POST /v1/public/auth/refresh
```

**User Model:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "username": "johndoe",
  "role": "USER|ADMIN",
  "is_active": true,
  "email_verified": true
}
```

---

## 3. Authentication Gap Analysis

### 3.1 Current vs Target

| Feature | Current | Target | Gap |
|---------|---------|--------|-----|
| Auth Method | API Key | OAuth 2.0 + JWT | **High** |
| User Management | None | Full user DB | **High** |
| Registration | None | Email + OAuth | **High** |
| Password Reset | None | Email-based | **Medium** |
| Email Verification | None | Token-based | **Medium** |
| Token Refresh | None | Built-in | **Medium** |
| OAuth Providers | None | GitHub, LinkedIn | **Medium** |
| Role-Based Access | None | USER/ADMIN roles | **Medium** |
| Session Management | None | JWT-based | **Medium** |

### 3.2 Required Changes

#### 3.2.1 Configuration (.env)

**Add:**
```bash
# AINative Authentication
AINATIVE_API_URL=https://api.ainative.studio/
AINATIVE_API_TOKEN=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
AINATIVE_USERNAME=admin@ainative.studio
AINATIVE_PASSWORD=Admin2025!Secure

# ZeroDB Project
ZERODB_PROJECT_ID=proj_123abc
```

#### 3.2.2 New Dependencies

**Add to requirements.txt:**
```
httpx>=0.27.0          # For AINative API calls
python-jose[cryptography]>=3.3.0  # For JWT handling
passlib[bcrypt]>=1.7.4  # For password hashing (if needed)
```

#### 3.2.3 Authentication Service

**Create: `app/services/ainative_auth.py`**
```python
class AINativeAuthService:
    def __init__(self):
        self.base_url = settings.AINATIVE_API_URL
        self.api_token = settings.AINATIVE_API_TOKEN

    async def register_user(self, email: str, password: str, name: str):
        # POST /v1/public/auth/register

    async def login(self, email: str, password: str):
        # POST /v1/public/auth/login-json
        # Returns access_token

    async def get_current_user(self, access_token: str):
        # GET /v1/public/auth/me

    async def refresh_token(self, refresh_token: str):
        # POST /v1/public/auth/refresh

    async def verify_token(self, token: str) -> dict:
        # Validate JWT and return user data
```

#### 3.2.4 FastAPI Dependencies

**Update: `app/api/deps.py`**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Validate JWT token and return user."""
    token = credentials.credentials
    auth_service = AINativeAuthService()

    try:
        user = await auth_service.verify_token(token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def get_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Ensure user is an admin."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

#### 3.2.5 New Auth Endpoints

**Create: `app/api/v1/endpoints/auth.py`**
```python
@router.post("/auth/register")
async def register(user: UserRegister):
    # Proxy to AINative auth

@router.post("/auth/login")
async def login(credentials: UserLogin):
    # Proxy to AINative auth

@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # Return current user info

@router.post("/auth/refresh")
async def refresh(refresh_token: str):
    # Proxy to AINative refresh
```

### 3.3 Migration Impact

**Breaking Changes:**
- All admin endpoints now require `Authorization: Bearer TOKEN` instead of `X-API-Key`
- Public endpoints can optionally use auth for user-specific features
- Existing API key integrations must migrate to OAuth flow

**Backward Compatibility:**
- Keep X-API-Key for 3 months with deprecation warning
- Support dual authentication during transition period

---

## 4. Database Gap Analysis

### 4.1 PostgreSQL vs ZeroDB Tables

| Feature | PostgreSQL + SQLAlchemy | ZeroDB Tables | Migration Complexity |
|---------|-------------------------|---------------|---------------------|
| Schema | Strict, typed columns | Flexible JSON documents | **High** - need schema validation |
| Relationships | Foreign keys, joins | Manual via IDs, no joins | **High** - denormalize data |
| Transactions | ACID compliant | Eventual consistency | **Medium** - adjust logic |
| Queries | SQL with complex joins | MongoDB-style filters | **High** - rewrite queries |
| Migrations | Alembic versioned | Schema-less, no migrations | **Low** - no migration files |
| Indexes | B-tree, GiST, etc. | Field indexes | **Medium** - recreate indexes |
| Constraints | FK, unique, check | Application-level only | **High** - move to app layer |
| Aggregations | SQL GROUP BY, SUM, etc. | Limited aggregation | **Medium** - app-level aggregation |
| Full-text Search | PostgreSQL FTS | Use ZeroDB Vectors instead | **Medium** - new approach |

### 4.2 Data Model Mapping

#### 4.2.1 Product Model

**Current (SQLAlchemy):**
```python
class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    template_id: Mapped[UUID] = mapped_column(ForeignKey("templates.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    template: Mapped["Template"] = relationship(back_populates="products")
    option_sets: Mapped[List["OptionSet"]] = relationship(
        secondary="product_option_sets"
    )
```

**Target (ZeroDB Table):**
```json
{
  "table_name": "products",
  "schema": {
    "id": "string",
    "name": "string",
    "description": "string",
    "price": "number",
    "template_id": "string",
    "is_active": "boolean",
    "created_at": "string",
    "updated_at": "string",
    "template": "object",
    "option_sets": "array",
    "metadata": "object"
  },
  "indexes": ["id", "template_id", "is_active"]
}
```

**Migration Notes:**
- Denormalize template data into product document
- Store option_sets as embedded array instead of junction table
- UUID → string conversion
- Decimal → float (precision loss risk)

#### 4.2.2 Order Model

**Current (SQLAlchemy with relations):**
```python
class Order(Base):
    id: UUID
    user_email: str
    status: OrderStatus  # Enum
    total_amount: Decimal
    items: List[OrderItem]  # Relationship
    payment_events: List[PaymentEvent]  # Relationship
```

**Target (ZeroDB - Denormalized):**
```json
{
  "id": "uuid-string",
  "user_email": "user@example.com",
  "status": "paid",
  "total_amount": 99.99,
  "items": [
    {
      "product_id": "prod_123",
      "product_name": "Custom T-Shirt",
      "quantity": 2,
      "unit_price": 24.99,
      "customization": {...}
    }
  ],
  "payment_events": [
    {
      "event_type": "charge.succeeded",
      "amount": 99.99,
      "timestamp": "2026-02-16T10:00:00Z"
    }
  ],
  "created_at": "2026-02-16T09:30:00Z",
  "updated_at": "2026-02-16T10:00:00Z"
}
```

**Migration Strategy:**
- Embed order_items directly in order document
- Embed payment_events in order document
- No separate OrderItem or PaymentEvent tables

### 4.3 Query Migration Examples

#### Example 1: Get Product with Template

**Current (SQL Join):**
```python
def get_product(db: Session, product_id: UUID):
    return db.query(Product)\
        .options(joinedload(Product.template))\
        .filter(Product.id == product_id)\
        .first()
```

**Target (ZeroDB API):**
```python
async def get_product(project_id: str, product_id: str):
    url = f"{AINATIVE_API_URL}/v1/public/zerodb/{project_id}/database/tables/products/rows/{product_id}"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        product = response.json()

    # Template data already embedded in product document
    return product
```

#### Example 2: Filter Products by Price Range

**Current (SQL WHERE):**
```python
def get_products_by_price(db: Session, min_price: float, max_price: float):
    return db.query(Product)\
        .filter(Product.price >= min_price)\
        .filter(Product.price <= max_price)\
        .all()
```

**Target (ZeroDB Query):**
```python
async def get_products_by_price(project_id: str, min_price: float, max_price: float):
    url = f"{AINATIVE_API_URL}/v1/public/zerodb/{project_id}/database/tables/products/query"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    payload = {
        "filter": {
            "price": {
                "$gte": min_price,
                "$lte": max_price
            }
        },
        "limit": 100
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()
```

#### Example 3: Aggregate Order Totals (Sales Report)

**Current (SQL Aggregation):**
```python
def get_sales_report(db: Session, start_date: datetime, end_date: datetime):
    return db.query(
        func.sum(Order.total_amount).label("total_revenue"),
        func.count(Order.id).label("total_orders")
    ).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).first()
```

**Target (Application-Level Aggregation):**
```python
async def get_sales_report(project_id: str, start_date: str, end_date: str):
    # Query all orders in date range
    url = f"{AINATIVE_API_URL}/v1/public/zerodb/{project_id}/database/tables/orders/query"
    payload = {
        "filter": {
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        },
        "limit": 1000  # May need pagination for large datasets
    }

    response = await client.post(url, json=payload, headers=headers)
    orders = response.json()["results"]

    # Aggregate in application code
    total_revenue = sum(order["total_amount"] for order in orders)
    total_orders = len(orders)

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders
    }
```

**Note:** For complex aggregations, consider using ZeroDB PostgreSQL instance instead.

---

## 5. API Endpoint Mapping

### 5.1 Products Endpoints

| Current Endpoint | Method | New Backend | ZeroDB API | Changes Required |
|-----------------|--------|-------------|------------|------------------|
| `/products` | GET | List products | `GET /zerodb/{proj}/database/tables/products/query` | Add pagination, filters |
| `/products/{id}` | GET | Get product | `GET /zerodb/{proj}/database/tables/products/rows/{id}` | Minimal |
| `/products` | POST | Create product | `POST /zerodb/{proj}/database/tables/products/rows` | Remove FK validation |
| `/products/{id}` | PUT | Update product | `PUT /zerodb/{proj}/database/tables/products/rows/{id}` | Minimal |
| `/products/{id}` | DELETE | Delete product | `DELETE /zerodb/{proj}/database/tables/products/rows/{id}` | Handle cascade manually |

### 5.2 Orders Endpoints

| Current Endpoint | Method | New Backend | Changes |
|-----------------|--------|-------------|---------|
| `/cart/checkout` | POST | Create order | Denormalize order items into single document |
| `/orders/{id}` | GET | Get order | Include embedded items and payment events |
| `/orders/{id}/status` | PATCH | Update status | Use ZeroDB Events to publish status changes |

### 5.3 New Endpoints (Leveraging ZeroDB Features)

**Vector Search for Products:**
```
POST /products/search/semantic
{
  "query": "red cotton t-shirt",
  "limit": 10
}

Backend: POST /zerodb/{proj}/embeddings/search
```

**Event Subscription:**
```
POST /webhooks/subscribe
{
  "topic": "order.created",
  "webhook_url": "https://client.com/webhooks"
}

Backend: POST /zerodb/{proj}/database/events/subscriptions
```

---

## 6. Data Model Migration

### 6.1 Table Creation Scripts

**Products Table:**
```python
import httpx

async def create_products_table(project_id: str):
    url = f"{AINATIVE_API_URL}/v1/public/zerodb/{project_id}/database/tables"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    payload = {
        "name": "products",
        "schema": {
            "id": "string",
            "name": "string",
            "description": "string",
            "price": "number",
            "template_id": "string",
            "template_data": "object",
            "option_sets": "array",
            "is_active": "boolean",
            "created_at": "string",
            "updated_at": "string"
        },
        "indexes": ["id", "template_id", "is_active", "name"]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()
```

**Orders Table:**
```python
async def create_orders_table(project_id: str):
    payload = {
        "name": "orders",
        "schema": {
            "id": "string",
            "user_id": "string",
            "user_email": "string",
            "status": "string",
            "total_amount": "number",
            "items": "array",           # Denormalized order items
            "payment_events": "array",  # Denormalized payment events
            "shipping_address": "object",
            "billing_address": "object",
            "created_at": "string",
            "updated_at": "string"
        },
        "indexes": ["id", "user_id", "user_email", "status", "created_at"]
    }
    # ... similar API call
```

### 6.2 Data Migration Script

**Export from PostgreSQL:**
```python
# scripts/export_postgres_data.py
import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Product, Template, Order

def export_products():
    db = SessionLocal()
    products = db.query(Product).all()

    exported = []
    for product in products:
        exported.append({
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "template_id": str(product.template_id),
            "template_data": {
                "id": str(product.template.id),
                "name": product.template.name,
                "zones": product.template.zones
            },
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat()
        })

    return exported
```

**Import to ZeroDB:**
```python
# scripts/import_to_zerodb.py
async def import_products(project_id: str, products: list):
    url = f"{AINATIVE_API_URL}/v1/public/zerodb/{project_id}/database/tables/products/rows"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    async with httpx.AsyncClient() as client:
        for product in products:
            response = await client.post(url, json=product, headers=headers)
            print(f"Imported product: {product['name']}")
```

---

## 7. Code Changes Required

### 7.1 New Services

**Create: `app/services/zerodb_service.py`**
```python
class ZeroDBService:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.base_url = f"{settings.AINATIVE_API_URL}/v1/public/zerodb/{project_id}/database"
        self.headers = {"Authorization": f"Bearer {settings.AINATIVE_API_TOKEN}"}

    async def create_row(self, table: str, data: dict):
        url = f"{self.base_url}/tables/{table}/rows"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=self.headers)
            return response.json()

    async def query_rows(self, table: str, filter: dict, limit: int = 100):
        url = f"{self.base_url}/tables/{table}/query"
        payload = {"filter": filter, "limit": limit}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            return response.json()

    async def get_row(self, table: str, row_id: str):
        url = f"{self.base_url}/tables/{table}/rows/{row_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            return response.json()

    async def update_row(self, table: str, row_id: str, data: dict):
        url = f"{self.base_url}/tables/{table}/rows/{row_id}"
        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=data, headers=self.headers)
            return response.json()

    async def delete_row(self, table: str, row_id: str):
        url = f"{self.base_url}/tables/{table}/rows/{row_id}"
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self.headers)
            return response.json()
```

### 7.2 Replace CRUD Operations

**Before (`app/crud/product.py`):**
```python
def get_product(db: Session, product_id: UUID) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
```

**After (`app/services/product_service.py`):**
```python
class ProductService:
    def __init__(self, zerodb: ZeroDBService):
        self.zerodb = zerodb

    async def get_product(self, product_id: str) -> dict:
        return await self.zerodb.get_row("products", product_id)

    async def create_product(self, product: ProductCreate) -> dict:
        data = {
            "id": str(uuid.uuid4()),
            **product.dict(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        return await self.zerodb.create_row("products", data)
```

### 7.3 Update API Endpoints

**Before (`app/api/v1/endpoints/products.py`):**
```python
@router.get("/{product_id}")
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    product = crud.product.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
```

**After:**
```python
@router.get("/{product_id}")
async def get_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)  # New auth
):
    zerodb = ZeroDBService(settings.ZERODB_PROJECT_ID)
    product_service = ProductService(zerodb)

    try:
        product = await product_service.get_product(product_id)
        return product
    except Exception as e:
        raise HTTPException(status_code=404, detail="Product not found")
```

### 7.4 Remove Database Dependencies

**Delete:**
- `app/db/session.py` (SQLAlchemy session management)
- `app/models/*.py` (all SQLAlchemy models)
- `app/crud/*.py` (all CRUD operations)
- `alembic/` (migration scripts)
- `alembic.ini`

**Update:**
- `app/api/deps.py` - remove `get_db` dependency
- All endpoints - remove `db: Session = Depends(get_db)` parameters

---

## 8. Migration Strategy

### 8.1 Phase 1: Preparation (Week 1)

**Objectives:**
- Set up AINative account and project
- Create ZeroDB tables
- Implement authentication service
- Create ZeroDB wrapper service

**Tasks:**
1. Create AINative project via API
2. Generate API tokens
3. Create all required ZeroDB tables (products, orders, etc.)
4. Implement `AINativeAuthService`
5. Implement `ZeroDBService`
6. Update `app/core/config.py` with new settings
7. Add new dependencies to `requirements.txt`

**Deliverables:**
- ZeroDB tables created
- Authentication service implemented
- Configuration updated

### 8.2 Phase 2: Dual-Database Mode (Week 2-3)

**Objectives:**
- Run PostgreSQL and ZeroDB in parallel
- Implement data sync mechanism
- Gradual endpoint migration

**Tasks:**
1. Create data sync service (PostgreSQL → ZeroDB)
2. Migrate read-only endpoints first (GET /products, GET /orders)
3. Test with production traffic
4. Validate data consistency
5. Monitor performance metrics

**Deliverables:**
- Dual-write to both databases
- 50% of endpoints using ZeroDB

### 8.3 Phase 3: Full Migration (Week 4)

**Objectives:**
- Migrate all write operations to ZeroDB
- Deprecate PostgreSQL
- Full authentication migration

**Tasks:**
1. Migrate all remaining endpoints
2. Implement ZeroDB Events for webhooks
3. Migrate file storage to ZeroDB Files
4. Remove PostgreSQL dependencies
5. Update all tests to use ZeroDB

**Deliverables:**
- 100% ZeroDB usage
- PostgreSQL decommissioned
- All tests passing

### 8.4 Phase 4: Optimization (Week 5-6)

**Objectives:**
- Leverage ZeroDB advanced features
- Optimize queries and indexing
- Implement vector search

**Tasks:**
1. Implement semantic product search using vectors
2. Set up event subscriptions for real-time updates
3. Optimize data denormalization
4. Performance tuning
5. Documentation updates

**Deliverables:**
- Vector search enabled
- Event-driven architecture
- Performance benchmarks met

---

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Data loss during migration | **Critical** | Low | Dual-database mode, backups, rollback plan |
| Query performance degradation | **High** | Medium | Benchmark before migration, optimize indexes |
| Authentication downtime | **High** | Low | Phased rollout, backward compatibility |
| ZeroDB API rate limits | **Medium** | Medium | Implement caching, batch operations |
| Data consistency issues | **High** | Medium | Transaction simulation, eventual consistency handling |
| Complex query limitations | **Medium** | High | Use PostgreSQL instance for analytics |
| Decimal precision loss | **Medium** | High | Use string representation for prices |

### 9.2 Business Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Extended migration timeline | Revenue impact | Phased approach, dual-mode operation |
| Customer-facing bugs | Reputation damage | Comprehensive testing, gradual rollout |
| Vendor lock-in | Strategic flexibility | Abstract data layer, maintain export capability |
| Cost overruns | Budget impact | Monitor usage, optimize queries |

---

## 10. Recommendations

### 10.1 Immediate Actions

1. **Start with Authentication**: Implement AINative OAuth first as a standalone change
2. **Create Sandbox Project**: Test ZeroDB capabilities before production migration
3. **Audit Complex Queries**: Identify queries that won't translate well to NoSQL
4. **Plan Data Denormalization**: Design embedded document structures

### 10.2 Architecture Decisions

**Hybrid Approach (Recommended):**
- Use **ZeroDB Tables** for operational data (products, orders, sessions)
- Use **ZeroDB PostgreSQL** for analytics and complex reporting
- Use **ZeroDB Vectors** for semantic search and recommendations
- Use **ZeroDB Events** for webhooks and pub/sub
- Use **ZeroDB Files** for media storage

**Benefits:**
- Best of both worlds (NoSQL flexibility + SQL analytics)
- Gradual migration path
- Reduced risk

### 10.3 Alternative Approach: Keep PostgreSQL

If migration risks are too high, consider:
- Keep PostgreSQL as primary database
- Use AINative for authentication only
- Use ZeroDB Vectors for semantic search (supplementary)
- Use ZeroDB Files for media storage (supplementary)

**Benefits:**
- Lower migration risk
- Preserve existing investment
- Still gain authentication and vector search capabilities

### 10.4 Success Metrics

**Performance:**
- API response time < 200ms (p95)
- Database query time < 50ms (p95)
- Zero data loss during migration

**Reliability:**
- 99.9% uptime during migration
- Zero authentication-related incidents
- Successful rollback capability maintained

**Business:**
- No customer-reported issues
- Migration completed within 6 weeks
- Cost reduction vs. current infrastructure

---

## Appendices

### A. AINative Credentials

```bash
# .env (already provided)
AINATIVE_USERNAME=admin@ainative.studio
AINATIVE_PASSWORD=Admin2025!Secure
AINATIVE_API_URL=https://api.ainative.studio/
AINATIVE_API_TOKEN=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
```

### B. Sample ZeroDB Service Wrapper

See `app/services/zerodb_service.py` in Section 7.1

### C. Testing Checklist

- [ ] Unit tests for all new services
- [ ] Integration tests for ZeroDB operations
- [ ] Authentication flow tests
- [ ] Performance benchmarks
- [ ] Data migration validation
- [ ] Rollback procedure tested
- [ ] Load testing at 2x expected traffic

### D. Rollback Plan

If migration fails:
1. Switch API endpoints back to PostgreSQL (flip feature flag)
2. Stop data sync to ZeroDB
3. Revert authentication to API key mode
4. Restore from PostgreSQL backup if needed
5. Post-mortem and plan adjustments

---

**Document Status**: Ready for Review
**Next Steps**: Schedule architecture review meeting with stakeholders
