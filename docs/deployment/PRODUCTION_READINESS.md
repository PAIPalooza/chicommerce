# ZeroCommerce Backend - Production Readiness Tracking

> **Platform Vision:** Microservices-only eCommerce platform for sites, apps, and experiences. Must be robust, type-safe, and deliver exceptional developer experience.

**Last Updated:** 2026-02-12
**Current Completion:** 35-40%
**Target:** 100% Production Ready
**Estimated Timeline:** 10 weeks

---

## Quick Stats

| Category | Progress | Critical Issues |
|----------|----------|-----------------|
| Core Models & Data | 70% | 4 missing models |
| API Endpoints | 50% | 8 critical endpoints missing |
| Type Safety | 40% | Inconsistent typing throughout |
| Security | 30% | 6 critical vulnerabilities |
| Testing | 30% | ~50% coverage gap |
| DevOps | 0% | No deployment infrastructure |
| Monitoring | 5% | No observability |
| Documentation | 40% | Missing API specs |

---

## 🔴 PRIORITY 1: BLOCKING ISSUES

### Issue #1: Order Management System (0% Complete)
**Status:** ❌ Not Started
**Priority:** P0 - BLOCKING
**Estimated Effort:** 2-3 weeks
**Assignee:** TBD

**Description:**
Cannot process customer orders - business cannot operate without this core functionality.

**Requirements:**
- [ ] Create comprehensive Order model with type safety
- [ ] Create OrderItem model with proper relationships
- [ ] Implement order lifecycle state machine (Created → Paid → Processing → Shipped → Delivered → Completed)
- [ ] Build order validation service
- [ ] Add order query endpoints with filtering
- [ ] Implement order status transitions with business rules
- [ ] Add order cancellation logic
- [ ] Create order history tracking

**Files to Create:**
```
app/models/order.py
app/models/order_item.py
app/schemas/order.py
app/schemas/order_item.py
app/crud/order.py
app/services/order.py
app/api/v1/endpoints/orders.py
app/api/v1/endpoints/checkout.py
tests/api/test_orders.py
tests/api/test_checkout.py
tests/unit/test_order_service.py
```

**Type Safety Requirements:**
```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class OrderCreate(BaseModel):
    cart_id: UUID
    shipping_address: ShippingAddress
    billing_address: Optional[BillingAddress] = None
    payment_method: PaymentMethod

    @validator('cart_id')
    def validate_cart_not_empty(cls, v, values):
        # Validation logic
        return v

class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    status: OrderStatus
    items: List[OrderItem]
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
```

**API Endpoints:**
- `POST /api/v1/checkout` - Create order from cart
- `GET /api/v1/orders` - List user orders (with pagination)
- `GET /api/v1/orders/{order_id}` - Get order details
- `PUT /api/v1/orders/{order_id}/cancel` - Cancel order
- `GET /api/v1/orders/{order_id}/status` - Get order status
- `GET /api/v1/admin/orders` - Admin: List all orders (with filtering)
- `PUT /api/v1/admin/orders/{order_id}/status` - Admin: Update order status

**Acceptance Criteria:**
- [ ] All endpoints return proper typed responses
- [ ] Order state transitions enforce business rules
- [ ] Cannot transition from SHIPPED to PAID
- [ ] Inventory is reserved on order creation
- [ ] Inventory is released on cancellation
- [ ] Test coverage > 90%
- [ ] OpenAPI docs generated correctly
- [ ] Response time < 100ms for order retrieval

---

### Issue #2: Payment Integration System (0% Complete)
**Status:** ❌ Not Started
**Priority:** P0 - BLOCKING
**Estimated Effort:** 2-3 weeks
**Assignee:** TBD

**Description:**
Cannot collect payments - no revenue generation possible. Must support multiple payment providers.

**Requirements:**
- [ ] Design payment service abstraction layer
- [ ] Integrate Stripe SDK with type-safe wrappers
- [ ] Integrate PayPal SDK with type-safe wrappers
- [ ] Implement payment intent creation
- [ ] Build webhook verification and handlers
- [ ] Add payment failure handling and retry logic
- [ ] Implement refund processing
- [ ] Add payment reconciliation
- [ ] Build payment audit logging
- [ ] Add idempotency keys for payment safety

**Files to Create:**
```
app/services/payment/__init__.py
app/services/payment/base.py
app/services/payment/stripe_provider.py
app/services/payment/paypal_provider.py
app/services/payment/types.py
app/models/payment.py
app/models/payment_transaction.py
app/schemas/payment.py
app/api/v1/endpoints/payment.py
app/api/v1/endpoints/webhooks.py
tests/unit/test_payment_service.py
tests/integration/test_stripe_integration.py
tests/integration/test_paypal_integration.py
```

**Type Safety Requirements:**
```python
from abc import ABC, abstractmethod
from typing import Protocol, Union
from decimal import Decimal

class PaymentProvider(Protocol):
    """Payment provider interface for type safety"""

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        metadata: dict[str, str]
    ) -> PaymentIntent: ...

    async def capture_payment(
        self,
        payment_intent_id: str
    ) -> PaymentResult: ...

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None
    ) -> RefundResult: ...

    async def verify_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> bool: ...

class PaymentIntent(BaseModel):
    id: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    client_secret: str
    created_at: datetime

class PaymentResult(BaseModel):
    success: bool
    payment_id: str
    amount: Decimal
    status: PaymentStatus
    error: Optional[str] = None

    @validator('amount')
    def validate_positive_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
```

**API Endpoints:**
- `POST /api/v1/payment/intent` - Create payment intent
- `POST /api/v1/payment/{payment_id}/capture` - Capture payment
- `POST /api/v1/payment/{payment_id}/refund` - Refund payment
- `POST /api/v1/webhooks/stripe` - Stripe webhook handler
- `POST /api/v1/webhooks/paypal` - PayPal webhook handler
- `GET /api/v1/admin/payments` - Admin: List payments

**Environment Variables Required:**
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
PAYPAL_CLIENT_ID=...
PAYPAL_SECRET=...
PAYPAL_MODE=sandbox  # or production
PAYMENT_RETRY_ATTEMPTS=3
PAYMENT_TIMEOUT_SECONDS=30
```

**Acceptance Criteria:**
- [ ] Supports both Stripe and PayPal
- [ ] All payment operations are type-safe
- [ ] Webhook signatures verified
- [ ] Idempotent payment processing
- [ ] Automatic retry on transient failures
- [ ] PCI compliance considerations documented
- [ ] Payment logs include audit trail
- [ ] Test coverage > 95% (critical path)
- [ ] Load tested to 1000 payments/minute

---

### Issue #3: Inventory Management System (0% Complete)
**Status:** ❌ Not Started
**Priority:** P0 - BLOCKING
**Estimated Effort:** 1 week
**Assignee:** TBD

**Description:**
No stock tracking leads to overselling and customer dissatisfaction. Must implement robust inventory system.

**Requirements:**
- [ ] Create Inventory model with proper constraints
- [ ] Implement atomic stock reservation
- [ ] Add stock release on order cancellation
- [ ] Build low stock alert system
- [ ] Add inventory adjustment endpoints (admin)
- [ ] Implement inventory history tracking
- [ ] Add concurrent stock update handling
- [ ] Build inventory synchronization service

**Files to Create:**
```
app/models/inventory.py
app/models/inventory_transaction.py
app/schemas/inventory.py
app/services/inventory.py
app/crud/inventory.py
app/api/v1/endpoints/inventory.py
tests/unit/test_inventory_service.py
tests/integration/test_inventory_concurrency.py
```

**Type Safety Requirements:**
```python
from decimal import Decimal
from typing import Literal

class InventoryTransactionType(str, Enum):
    RESTOCK = "restock"
    SALE = "sale"
    RESERVATION = "reservation"
    RELEASE = "release"
    ADJUSTMENT = "adjustment"
    DAMAGED = "damaged"

class InventoryModel(Base):
    __tablename__ = "inventory"

    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True
    )
    quantity: Mapped[int] = mapped_column(
        CheckConstraint('quantity >= 0', name='inventory_quantity_positive'),
        nullable=False,
        default=0
    )
    reserved: Mapped[int] = mapped_column(
        CheckConstraint('reserved >= 0', name='inventory_reserved_positive'),
        nullable=False,
        default=0
    )
    available: Mapped[int] = mapped_column(Computed('quantity - reserved'))
    low_stock_threshold: Mapped[int] = mapped_column(default=10)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

class StockReservation(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)
    order_id: UUID
    expires_at: datetime

class InventoryService:
    async def reserve_stock(
        self,
        db: AsyncSession,
        product_id: UUID,
        quantity: int,
        order_id: UUID
    ) -> Result[StockReservation, InventoryError]:
        """
        Atomically reserve stock for an order.
        Returns Result type for type-safe error handling.
        """
        ...
```

**API Endpoints:**
- `GET /api/v1/inventory/{product_id}` - Get product inventory
- `POST /api/v1/admin/inventory/{product_id}/adjust` - Adjust inventory
- `GET /api/v1/admin/inventory/low-stock` - Get low stock products
- `GET /api/v1/admin/inventory/history/{product_id}` - Get inventory history

**Database Constraints:**
```sql
-- Add to migration
ALTER TABLE inventory ADD CONSTRAINT inventory_available_check
    CHECK ((quantity - reserved) >= 0);

CREATE INDEX idx_inventory_low_stock
    ON inventory(product_id)
    WHERE (quantity - reserved) <= low_stock_threshold;
```

**Acceptance Criteria:**
- [ ] Stock reservations are atomic (no race conditions)
- [ ] Cannot oversell (quantity - reserved always >= 0)
- [ ] Expired reservations auto-release
- [ ] Low stock alerts trigger webhooks
- [ ] Concurrent updates tested with 100+ threads
- [ ] Test coverage > 95%
- [ ] All operations return typed Results

---

### Issue #4: Webhook System & Event Publishing (0% Complete)
**Status:** ❌ Not Started
**Priority:** P0 - BLOCKING
**Estimated Effort:** 1-2 weeks
**Assignee:** TBD

**Description:**
Cannot integrate with fulfillment services or notify partners. Need robust webhook delivery system.

**Requirements:**
- [ ] Create WebhookLog model with delivery tracking
- [ ] Build webhook registration system
- [ ] Implement reliable delivery with retries
- [ ] Add webhook signature verification
- [ ] Build webhook event types system
- [ ] Implement dead letter queue
- [ ] Add webhook testing endpoint
- [ ] Build webhook replay functionality

**Files to Create:**
```
app/models/webhook_log.py
app/models/webhook_subscription.py
app/schemas/webhook.py
app/services/webhook.py
app/services/event_publisher.py
app/api/v1/endpoints/webhooks.py
app/api/v1/endpoints/webhook_subscriptions.py
tests/unit/test_webhook_service.py
tests/integration/test_webhook_delivery.py
```

**Type Safety Requirements:**
```python
from typing import Literal, TypedDict

class WebhookEventType(str, Enum):
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"
    ORDER_CANCELLED = "order.cancelled"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    INVENTORY_LOW = "inventory.low"
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"

class WebhookPayload(BaseModel):
    id: UUID
    event: WebhookEventType
    timestamp: datetime
    data: dict[str, Any]
    signature: str

    class Config:
        frozen = True  # Immutable

class WebhookSubscription(BaseModel):
    id: UUID
    endpoint: HttpUrl
    events: set[WebhookEventType]
    secret: str
    is_active: bool
    retry_config: RetryConfig

    @validator('endpoint')
    def validate_https(cls, v):
        if not str(v).startswith('https://'):
            raise ValueError('Webhook endpoints must use HTTPS')
        return v

class RetryConfig(BaseModel):
    max_attempts: int = Field(default=5, ge=1, le=10)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=5.0)
    initial_delay_seconds: int = Field(default=60, ge=1, le=3600)

class WebhookDeliveryResult(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    attempted_at: datetime
    next_retry_at: Optional[datetime] = None
```

**Service Implementation:**
```python
class WebhookService:
    def __init__(self, db: AsyncSession, http_client: httpx.AsyncClient):
        self.db = db
        self.http_client = http_client

    async def publish_event(
        self,
        event_type: WebhookEventType,
        data: dict[str, Any]
    ) -> list[UUID]:
        """
        Publish event to all subscribed endpoints.
        Returns list of delivery job IDs.
        """
        subscriptions = await self._get_active_subscriptions(event_type)
        job_ids = []

        for sub in subscriptions:
            payload = self._create_payload(event_type, data, sub.secret)
            job_id = await self._enqueue_delivery(sub, payload)
            job_ids.append(job_id)

        return job_ids

    async def deliver_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload
    ) -> WebhookDeliveryResult:
        """
        Deliver webhook with retry logic.
        """
        ...
```

**API Endpoints:**
- `POST /api/v1/admin/webhook-subscriptions` - Create webhook subscription
- `GET /api/v1/admin/webhook-subscriptions` - List subscriptions
- `PUT /api/v1/admin/webhook-subscriptions/{id}` - Update subscription
- `DELETE /api/v1/admin/webhook-subscriptions/{id}` - Delete subscription
- `POST /api/v1/admin/webhook-subscriptions/{id}/test` - Test webhook
- `POST /api/v1/admin/webhook-logs/{id}/replay` - Replay failed webhook
- `GET /api/v1/admin/webhook-logs` - List webhook delivery logs

**Acceptance Criteria:**
- [ ] Webhook deliveries are reliable (retry with exponential backoff)
- [ ] All payloads signed with HMAC-SHA256
- [ ] Dead letter queue for failed deliveries
- [ ] Delivery logs retained for 90 days
- [ ] Test endpoint validates connectivity
- [ ] Support for replay after fixes
- [ ] Test coverage > 90%
- [ ] Handle 1000+ events/second

---

### Issue #5: Type Safety Overhaul (40% Complete)
**Status:** 🟡 In Progress
**Priority:** P0 - BLOCKING
**Estimated Effort:** 1 week
**Assignee:** TBD

**Description:**
Inconsistent type hints throughout codebase. For a microservices platform, type safety is critical for developer experience and reducing runtime errors.

**Requirements:**
- [ ] Add strict type hints to all functions
- [ ] Enable mypy strict mode
- [ ] Add type stubs for external libraries
- [ ] Use Pydantic models everywhere
- [ ] Add return type annotations
- [ ] Fix all mypy errors
- [ ] Add type guards where needed
- [ ] Use Protocol for interfaces

**Files to Update:**
```
ALL Python files in:
  app/crud/
  app/services/
  app/api/
  app/core/
  tests/
```

**Mypy Configuration:**
```ini
# mypy.ini
[mypy]
python_version = 3.11
strict = True
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_any_generics = True
disallow_subclassing_any = True
disallow_untyped_calls = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
```

**Examples of Required Changes:**

**Before:**
```python
# app/crud/product.py
def get_product(db, product_id):
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(db, product_in):
    product = Product(**product_in.dict())
    db.add(product)
    db.commit()
    return product
```

**After:**
```python
# app/crud/product.py
from typing import Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate

def get_product(
    db: Session,
    product_id: UUID
) -> Optional[Product]:
    """
    Retrieve a product by ID.

    Args:
        db: Database session
        product_id: UUID of the product

    Returns:
        Product if found, None otherwise
    """
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(
    db: Session,
    product_in: ProductCreate
) -> Product:
    """
    Create a new product.

    Args:
        db: Database session
        product_in: Product creation schema

    Returns:
        Created product instance

    Raises:
        ValueError: If product name already exists
    """
    product = Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
```

**Protocol Usage:**
```python
# app/services/protocols.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class PaymentProvider(Protocol):
    async def create_payment(
        self,
        amount: Decimal,
        currency: str
    ) -> PaymentResult: ...

    async def refund_payment(
        self,
        payment_id: str,
        amount: Decimal
    ) -> RefundResult: ...
```

**CI Integration:**
```yaml
# .github/workflows/type-check.yml
name: Type Check
on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install mypy types-all
      - run: mypy app/ --strict
```

**Acceptance Criteria:**
- [ ] 100% of functions have type hints
- [ ] `mypy --strict` passes with zero errors
- [ ] All Pydantic models use Field validators
- [ ] Protocols used for all interfaces
- [ ] Type stubs added for untyped libraries
- [ ] CI fails on type errors
- [ ] Developer docs updated with typing guide

---

### Issue #6: Security Hardening (30% Complete)
**Status:** 🟡 In Progress
**Priority:** P0 - BLOCKING
**Estimated Effort:** 2 weeks
**Assignee:** TBD

**Description:**
Multiple critical security vulnerabilities that make the system unsafe for production use.

**Critical Vulnerabilities Found:**

#### 6.1: Timing Attack in API Key Validation
**Location:** `app/core/security.py:28`
**Severity:** HIGH

**Current Code:**
```python
def verify_api_key(api_key: str) -> bool:
    return api_key == settings.ADMIN_API_KEY  # ❌ Timing attack
```

**Fix:**
```python
import secrets

def verify_api_key(api_key: str) -> bool:
    """
    Verify API key using constant-time comparison.
    Prevents timing attacks.
    """
    return secrets.compare_digest(api_key, settings.ADMIN_API_KEY)
```

#### 6.2: Weak Session ID Generation
**Location:** `app/api/v1/endpoints/cart.py:40`
**Severity:** HIGH

**Current Code:**
```python
session_id = str(hash(request.client.host + str(request.url)))  # ❌ Predictable
```

**Fix:**
```python
import secrets

def generate_session_id() -> str:
    """Generate cryptographically secure session ID."""
    return secrets.token_urlsafe(32)
```

#### 6.3: Missing Rate Limiting
**Severity:** HIGH

**Fix:**
```python
# app/core/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="redis://localhost:6379"
)

# app/main.py
from app.core.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# In endpoints:
@router.post("/checkout")
@limiter.limit("5/minute")  # Max 5 checkouts per minute per IP
async def checkout(...):
    ...
```

#### 6.4: No Input Sanitization
**Severity:** MEDIUM

**Fix:**
```python
# app/core/sanitize.py
import bleach
from typing import Any

ALLOWED_TAGS = []  # No HTML allowed
ALLOWED_ATTRIBUTES = {}

def sanitize_html(text: str) -> str:
    """Remove all HTML tags from user input."""
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize all string values in dict."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_html(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item) if isinstance(item, dict)
                else sanitize_html(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized

# In Pydantic models:
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None

    @validator('name', 'description')
    def sanitize_text(cls, v):
        if v:
            return sanitize_html(v)
        return v
```

#### 6.5: Missing Security Headers
**Severity:** MEDIUM

**Fix:**
```python
# app/core/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response

# app/main.py
app.add_middleware(SecurityHeadersMiddleware)
```

#### 6.6: SQL Injection Prevention Audit
**Severity:** MEDIUM

**Tasks:**
- [ ] Audit all raw SQL queries
- [ ] Ensure all queries use parameterization
- [ ] Add SQLAlchemy query logging in dev
- [ ] Run sqlmap security tests

**Requirements:**
- [ ] Fix timing attack vulnerability
- [ ] Implement rate limiting on all endpoints
- [ ] Add input sanitization middleware
- [ ] Implement security headers
- [ ] Use cryptographically secure session IDs
- [ ] Add CSRF protection for state-changing operations
- [ ] Implement API key rotation mechanism
- [ ] Add brute force protection on auth endpoints
- [ ] Audit all SQL queries for injection risks
- [ ] Add security.txt file
- [ ] Document security practices

**Files to Create/Update:**
```
app/core/rate_limit.py
app/core/sanitize.py
app/core/security_headers.py
app/core/csrf.py
app/core/security.py (update)
.well-known/security.txt
SECURITY.md
```

**Dependencies to Add:**
```txt
slowapi>=0.1.9
bleach>=6.1.0
python-multipart>=0.0.6
```

**Acceptance Criteria:**
- [ ] All vulnerabilities fixed
- [ ] Rate limiting active on all endpoints
- [ ] Security headers on all responses
- [ ] Input sanitization on all user input
- [ ] OWASP Top 10 compliance verified
- [ ] Security audit passed
- [ ] Penetration test passed

---

### Issue #7: Deployment Infrastructure (0% Complete)
**Status:** ❌ Not Started
**Priority:** P0 - BLOCKING
**Estimated Effort:** 1-2 weeks
**Assignee:** TBD

**Description:**
No way to deploy to production. Need complete Docker, CI/CD, and orchestration setup.

**Requirements:**
- [ ] Create production-ready Dockerfile
- [ ] Build docker-compose for local development
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Create Kubernetes manifests
- [ ] Add health check endpoints
- [ ] Implement graceful shutdown
- [ ] Add database migration automation
- [ ] Create environment-specific configs

**Files to Create:**
```
Dockerfile
.dockerignore
docker-compose.yml
docker-compose.dev.yml
docker-compose.prod.yml
.github/workflows/ci.yml
.github/workflows/deploy-staging.yml
.github/workflows/deploy-prod.yml
kubernetes/namespace.yml
kubernetes/deployment.yml
kubernetes/service.yml
kubernetes/ingress.yml
kubernetes/secrets.yml
kubernetes/configmap.yml
helm/Chart.yaml
helm/values.yaml
helm/values-staging.yaml
helm/values-prod.yaml
scripts/deploy.sh
scripts/rollback.sh
```

**Dockerfile (Multi-stage):**
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy application
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/zerocommerce
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=zerocommerce
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  migrations:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/zerocommerce
    depends_on:
      db:
        condition: service_healthy
    command: alembic upgrade head

volumes:
  postgres_data:
  redis_data:
```

**GitHub Actions CI:**
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: zerocommerce_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio

    - name: Run type check
      run: mypy app/ --strict

    - name: Run linters
      run: |
        black --check app/ tests/
        isort --check-only app/ tests/
        flake8 app/ tests/

    - name: Run tests
      env:
        DATABASE_URL: postgresql+psycopg2://postgres:postgres@localhost:5432/zerocommerce_test
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        ADMIN_API_KEY: test-admin-key
      run: |
        pytest --cov=app --cov-report=xml --cov-report=term-missing

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Build Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: false
        tags: zerocommerce:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

**Kubernetes Deployment:**
```yaml
# kubernetes/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zerocommerce-api
  namespace: zerocommerce
  labels:
    app: zerocommerce-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: zerocommerce-api
  template:
    metadata:
      labels:
        app: zerocommerce-api
    spec:
      containers:
      - name: api
        image: zerocommerce:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: zerocommerce-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: zerocommerce-secrets
              key: redis-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: zerocommerce-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      initContainers:
      - name: migrations
        image: zerocommerce:latest
        command: ["alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: zerocommerce-secrets
              key: database-url
```

**Health Check Endpoints:**
```python
# app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from redis import Redis

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check - service is running"""
    return {"status": "ok"}

@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Readiness check - service can handle requests"""
    try:
        # Check database
        db.execute(text("SELECT 1"))

        # Check Redis
        redis.ping()

        return {
            "status": "ready",
            "database": "connected",
            "cache": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not ready",
                "error": str(e)
            }
        )

@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness check - service should be restarted if fails"""
    return {"status": "alive"}
```

**Acceptance Criteria:**
- [ ] Docker image builds successfully
- [ ] docker-compose runs full stack locally
- [ ] CI pipeline runs on every PR
- [ ] CI includes type checking, linting, tests
- [ ] Kubernetes manifests deploy successfully
- [ ] Health checks return correct status
- [ ] Graceful shutdown doesn't drop connections
- [ ] Zero-downtime deployments work
- [ ] Rollback procedure tested
- [ ] Database migrations run automatically

---

## 🟠 PRIORITY 2: HIGH IMPORTANCE

### Issue #8: Services Layer Architecture (0% Complete)
**Status:** ❌ Not Started
**Priority:** P1 - HIGH
**Estimated Effort:** 2 weeks
**Assignee:** TBD

**Description:**
Business logic is scattered throughout API endpoints. Need clean service layer for maintainability.

**Current Problems:**
- `app/api/v1/endpoints/cart.py:303` - Inline price calculation
- No separation of concerns
- Hard to test business logic
- Code duplication

**Service Layer Architecture:**
```
app/services/
├── __init__.py
├── base.py              # Base service class
├── pricing.py           # Price calculation service
├── tax.py              # Tax calculation service
├── shipping.py         # Shipping calculation service
├── validation.py       # Customization validation service
├── inventory.py        # Inventory management service
├── order.py           # Order processing service
├── payment.py         # Payment processing service
├── webhook.py         # Webhook delivery service
├── notification.py    # Email/SMS notifications
└── preview.py         # Preview generation service
```

**Base Service Pattern:**
```python
# app/services/base.py
from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseService(Generic[T]):
    """Base service class with common patterns"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID"""
        raise NotImplementedError

    async def create(self, data: BaseModel) -> T:
        """Create new entity"""
        raise NotImplementedError

    async def update(self, id: UUID, data: BaseModel) -> T:
        """Update entity"""
        raise NotImplementedError

    async def delete(self, id: UUID) -> bool:
        """Delete entity"""
        raise NotImplementedError
```

**Pricing Service:**
```python
# app/services/pricing.py
from decimal import Decimal
from typing import Protocol

class TaxCalculator(Protocol):
    async def calculate_tax(
        self,
        subtotal: Decimal,
        shipping_address: Address
    ) -> Decimal: ...

class ShippingCalculator(Protocol):
    async def calculate_shipping(
        self,
        items: list[CartItem],
        destination: Address
    ) -> Decimal: ...

class PricingService:
    def __init__(
        self,
        tax_calculator: TaxCalculator,
        shipping_calculator: ShippingCalculator
    ):
        self.tax_calculator = tax_calculator
        self.shipping_calculator = shipping_calculator

    async def calculate_cart_total(
        self,
        cart: Cart,
        shipping_address: Address
    ) -> PriceBreakdown:
        """
        Calculate complete cart pricing.

        Returns type-safe price breakdown.
        """
        # Calculate subtotal
        subtotal = sum(
            item.quantity * item.unit_price
            for item in cart.items
        )

        # Calculate tax
        tax = await self.tax_calculator.calculate_tax(
            subtotal,
            shipping_address
        )

        # Calculate shipping
        shipping = await self.shipping_calculator.calculate_shipping(
            cart.items,
            shipping_address
        )

        # Calculate total
        total = subtotal + tax + shipping

        return PriceBreakdown(
            subtotal=subtotal,
            tax=tax,
            shipping=shipping,
            total=total,
            currency="USD"
        )

class PriceBreakdown(BaseModel):
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    discount: Decimal = Decimal("0.00")
    total: Decimal
    currency: str

    @validator('subtotal', 'tax', 'shipping', 'total')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative')
        return v

    @validator('total')
    def validate_total(cls, v, values):
        expected = (
            values.get('subtotal', 0) +
            values.get('tax', 0) +
            values.get('shipping', 0) -
            values.get('discount', 0)
        )
        if abs(v - expected) > Decimal('0.01'):
            raise ValueError('Total does not match breakdown')
        return v
```

**Validation Service:**
```python
# app/services/validation.py
from typing import Any

class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class ValidationResult:
    def __init__(self):
        self.errors: list[ValidationError] = []

    def add_error(self, field: str, message: str) -> None:
        self.errors.append(ValidationError(field, message))

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            raise HTTPException(
                status_code=400,
                detail=[
                    {"field": e.field, "message": e.message}
                    for e in self.errors
                ]
            )

class CustomizationValidationService:
    async def validate_customization(
        self,
        template: Template,
        customization_data: dict[str, Any]
    ) -> ValidationResult:
        """
        Validate customization data against template constraints.
        """
        result = ValidationResult()

        for zone in template.customization_zones:
            value = customization_data.get(zone.key)

            if zone.type == "text":
                self._validate_text_zone(zone, value, result)
            elif zone.type == "image":
                await self._validate_image_zone(zone, value, result)
            elif zone.type == "color":
                self._validate_color_zone(zone, value, result)

        return result

    def _validate_text_zone(
        self,
        zone: CustomizationZone,
        value: Optional[str],
        result: ValidationResult
    ) -> None:
        if not value:
            if zone.config.get('required', False):
                result.add_error(zone.key, "Text is required")
            return

        max_length = zone.config.get('max_length')
        if max_length and len(value) > max_length:
            result.add_error(
                zone.key,
                f"Text exceeds maximum length of {max_length}"
            )
```

**Refactored Endpoint:**
```python
# app/api/v1/endpoints/cart.py (after refactor)
from app.services.pricing import PricingService
from app.services.validation import CustomizationValidationService

@router.post("/cart/items", response_model=CartResponse)
async def add_item_to_cart(
    item_in: CartItemCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    pricing_service: PricingService = Depends(deps.get_pricing_service),
    validation_service: CustomizationValidationService = Depends(deps.get_validation_service)
):
    """Add item to cart with proper service layer"""

    # Validate customization
    template = await get_template(db, item_in.template_id)
    validation_result = await validation_service.validate_customization(
        template,
        item_in.customization_data
    )
    validation_result.raise_if_invalid()

    # Calculate price
    price = await pricing_service.calculate_item_price(
        product_id=item_in.product_id,
        options=item_in.options,
        quantity=item_in.quantity
    )

    # Add to cart
    cart = await cart_crud.add_item(
        db,
        cart_id=get_cart_id(request),
        item_in=item_in,
        unit_price=price.unit_price
    )

    return cart
```

**Acceptance Criteria:**
- [ ] All business logic moved to services
- [ ] Services are type-safe
- [ ] Services use dependency injection
- [ ] Services are independently testable
- [ ] Clear separation of concerns
- [ ] Zero business logic in endpoints
- [ ] All services have unit tests

---

### Issue #9: Error Handling & Structured Logging (20% Complete)
**Status:** 🟡 In Progress
**Priority:** P1 - HIGH
**Estimated Effort:** 1 week
**Assignee:** TBD

**Description:**
Poor error handling makes debugging production issues difficult. Using print() instead of proper logging.

**Current Issues:**
- `app/api/v1/endpoints/products.py:159` - Using print()
- `app/api/v1/endpoints/cart.py:81,99` - Multiple print() statements
- No structured logging
- Generic error messages
- No request tracing

**Requirements:**
- [ ] Replace all print() with proper logging
- [ ] Implement structured logging (JSON format)
- [ ] Add request ID tracking
- [ ] Integrate Sentry for error tracking
- [ ] Add global exception handlers
- [ ] Implement custom error types
- [ ] Add error codes for client reference
- [ ] Log all database queries in dev

**Files to Create/Update:**
```
app/core/logging.py
app/core/exceptions.py
app/core/error_handlers.py
app/middleware/request_id.py
app/middleware/logging_middleware.py
```

**Structured Logging Setup:**
```python
# app/core/logging.py
import logging
import sys
from typing import Any
import structlog

def setup_logging() -> None:
    """Configure structured logging"""

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
```

**Custom Exceptions:**
```python
# app/core/exceptions.py
from typing import Any, Optional

class ZeroCommerceException(Exception):
    """Base exception for all ZeroCommerce errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ProductNotFoundError(ZeroCommerceException):
    def __init__(self, product_id: UUID):
        super().__init__(
            message=f"Product {product_id} not found",
            error_code="PRODUCT_NOT_FOUND",
            status_code=404,
            details={"product_id": str(product_id)}
        )

class InsufficientStockError(ZeroCommerceException):
    def __init__(self, product_id: UUID, requested: int, available: int):
        super().__init__(
            message=f"Insufficient stock for product {product_id}",
            error_code="INSUFFICIENT_STOCK",
            status_code=400,
            details={
                "product_id": str(product_id),
                "requested": requested,
                "available": available
            }
        )

class PaymentFailedError(ZeroCommerceException):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Payment failed: {reason}",
            error_code="PAYMENT_FAILED",
            status_code=402,
            details={"reason": reason}
        )
```

**Global Exception Handler:**
```python
# app/core/error_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

async def zerocommerce_exception_handler(
    request: Request,
    exc: ZeroCommerceException
) -> JSONResponse:
    """Handle custom ZeroCommerce exceptions"""

    logger.error(
        "zerocommerce_error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method,
        request_id=request.state.request_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request.state.request_id
            }
        }
    )

async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions"""

    logger.exception(
        "unhandled_exception",
        exc_type=type(exc).__name__,
        exc_message=str(exc),
        path=request.url.path,
        method=request.method,
        request_id=request.state.request_id
    )

    # Send to Sentry
    if sentry_sdk:
        sentry_sdk.capture_exception(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request.state.request_id
            }
        }
    )

# app/main.py
from app.core.error_handlers import (
    zerocommerce_exception_handler,
    global_exception_handler
)

app.add_exception_handler(ZeroCommerceException, zerocommerce_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
```

**Request ID Middleware:**
```python
# app/middleware/request_id.py
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.state.request_id = request_id

        # Add to logging context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id

        return response
```

**Logging Middleware:**
```python
# app/middleware/logging_middleware.py
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params)
        )

        response = await call_next(request)

        process_time = time.time() - start_time

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=process_time
        )

        return response
```

**Sentry Integration:**
```python
# app/core/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def setup_sentry(dsn: str, environment: str) -> None:
    """Configure Sentry error tracking"""

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration()
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,
    )
```

**Updated Endpoint:**
```python
# app/api/v1/endpoints/products.py (fixed)
import structlog

logger = structlog.get_logger()

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: Session = Depends(deps.get_db),
    api_key: str = Depends(deps.get_admin_key)
) -> None:
    """Delete a product"""

    try:
        product_exists = crud.delete_product(db=db, product_id=product_id)
        if not product_exists:
            raise ProductNotFoundError(product_id)

        logger.info(
            "product_deleted",
            product_id=str(product_id)
        )

    except ProductNotFoundError:
        raise
    except Exception as e:
        logger.exception(
            "product_deletion_failed",
            product_id=str(product_id),
            error=str(e)
        )
        raise ZeroCommerceException(
            message="Failed to delete product",
            error_code="PRODUCT_DELETION_FAILED",
            status_code=500,
            details={"product_id": str(product_id)}
        )
```

**Dependencies to Add:**
```txt
structlog>=23.2.0
sentry-sdk[fastapi]>=1.40.0
```

**Acceptance Criteria:**
- [ ] Zero print() statements in codebase
- [ ] All logs in JSON format
- [ ] Request ID in all log entries
- [ ] Sentry captures all errors
- [ ] Custom error types for all business errors
- [ ] Error responses include error codes
- [ ] Database query logging in dev
- [ ] Log rotation configured

---

### Issue #10: Redis Caching Implementation (0% Complete)
**Status:** ❌ Not Started
**Priority:** P1 - HIGH
**Estimated Effort:** 1 week
**Assignee:** TBD

**Description:**
Redis configured but not implemented. Need caching for performance at scale.

**Requirements:**
- [ ] Initialize Redis client
- [ ] Create caching decorator
- [ ] Implement cache invalidation
- [ ] Add cache warming on startup
- [ ] Cache product list
- [ ] Cache templates
- [ ] Cache option sets
- [ ] Cache session data
- [ ] Add cache hit/miss metrics

**Files to Create:**
```
app/core/cache.py
app/services/cache.py
tests/unit/test_cache.py
tests/integration/test_redis_cache.py
```

**Redis Client Setup:**
```python
# app/core/cache.py
from typing import Any, Optional, Callable
from functools import wraps
import pickle
import hashlib
from redis.asyncio import Redis
import structlog

logger = structlog.get_logger()

class CacheClient:
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False  # Use bytes for pickle
        )

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug("cache_hit", key=key)
                return pickle.loads(data)
            logger.debug("cache_miss", key=key)
            return None
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """Set value in cache with TTL"""
        try:
            data = pickle.dumps(value)
            await self.redis.setex(key, ttl, data)
            logger.debug("cache_set", key=key, ttl=ttl)
            return True
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.redis.delete(key)
            logger.debug("cache_delete", key=key)
            return True
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                count = await self.redis.delete(*keys)
                logger.info("cache_pattern_delete", pattern=pattern, count=count)
                return count
            return 0
        except Exception as e:
            logger.error("cache_pattern_delete_error", pattern=pattern, error=str(e))
            return 0

# Global cache instance
cache: Optional[CacheClient] = None

def get_cache() -> CacheClient:
    """Dependency for cache client"""
    if cache is None:
        raise RuntimeError("Cache not initialized")
    return cache
```

**Caching Decorator:**
```python
# app/core/cache.py (continued)
from typing import TypeVar, Callable
import inspect

T = TypeVar('T')

def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    key_builder: Optional[Callable[..., str]] = None
):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        key_builder: Custom function to build cache key
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key: prefix:func_name:hash(args+kwargs)
                key_parts = [key_prefix, func.__name__]

                # Hash function arguments
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Create stable hash of arguments
                arg_str = str(sorted(bound_args.arguments.items()))
                arg_hash = hashlib.md5(arg_str.encode()).hexdigest()[:8]
                key_parts.append(arg_hash)

                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = await get_cache().get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await get_cache().set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
```

**Cache Warming:**
```python
# app/services/cache.py
class CacheWarmer:
    """Warm cache on application startup"""

    def __init__(
        self,
        db: AsyncSession,
        cache: CacheClient
    ):
        self.db = db
        self.cache = cache

    async def warm_all(self) -> None:
        """Warm all caches"""
        logger.info("cache_warming_started")

        await self.warm_products()
        await self.warm_templates()
        await self.warm_option_sets()

        logger.info("cache_warming_completed")

    async def warm_products(self) -> None:
        """Warm product cache"""
        products = await crud.get_products(self.db, active_only=True)
        for product in products:
            key = f"product:{product.id}"
            await self.cache.set(key, product, ttl=3600)
        logger.info("products_cached", count=len(products))

    async def warm_templates(self) -> None:
        """Warm template cache"""
        templates = await crud.get_all_templates(self.db)
        for template in templates:
            key = f"template:{template.id}"
            await self.cache.set(key, template, ttl=3600)
        logger.info("templates_cached", count=len(templates))
```

**Cached CRUD Operations:**
```python
# app/crud/product.py
from app.core.cache import cached

@cached(ttl=3600, key_prefix="product")
async def get_product(
    db: AsyncSession,
    product_id: UUID
) -> Optional[Product]:
    """Get product with caching"""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()

@cached(ttl=60, key_prefix="products:list")
async def get_products(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> list[Product]:
    """Get products list with caching"""
    query = select(Product)
    if active_only:
        query = query.where(Product.is_active == True)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
```

**Cache Invalidation:**
```python
# app/crud/product.py
from app.core.cache import get_cache

async def update_product(
    db: AsyncSession,
    product: Product,
    product_in: ProductUpdate
) -> Product:
    """Update product and invalidate cache"""

    # Update database
    for field, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    # Invalidate caches
    cache = get_cache()
    await cache.delete(f"product:{product.id}")
    await cache.delete_pattern("products:list:*")

    logger.info("product_cache_invalidated", product_id=str(product.id))

    return product
```

**Cache Metrics:**
```python
# app/core/cache.py (add to CacheClient)
from prometheus_client import Counter, Histogram

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['key_prefix']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['key_prefix']
)

cache_operation_duration = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration',
    ['operation']
)
```

**Dependencies:**
```txt
redis[async]>=5.0.1
```

**Acceptance Criteria:**
- [ ] Redis client initialized on startup
- [ ] Caching decorator works correctly
- [ ] Cache invalidation on updates
- [ ] Cache warming on startup
- [ ] Product list cached (60s TTL)
- [ ] Templates cached (5m TTL)
- [ ] Sessions cached (1h TTL)
- [ ] Cache hit/miss metrics exposed
- [ ] Performance tests show improvement

---

### Issue #11: Testing Coverage Expansion (30% → 80%+)
**Status:** 🟡 In Progress
**Priority:** P1 - HIGH
**Estimated Effort:** 2 weeks
**Assignee:** TBD

**Description:**
Current test coverage is only ~30-40%. Need comprehensive testing for production confidence.

**Current State:**
- ✅ 8 test files (~1700 lines)
- ✅ Basic fixtures
- ⚠️ Low coverage
- ❌ No payment tests
- ❌ No order tests
- ❌ No webhook tests
- ❌ No load tests

**Requirements:**
- [ ] Achieve 80%+ code coverage
- [ ] Add integration tests for all workflows
- [ ] Add end-to-end tests
- [ ] Add load tests
- [ ] Add security tests
- [ ] Add contract tests for APIs
- [ ] Set up coverage reporting in CI
- [ ] Add mutation testing

**Test Structure:**
```
tests/
├── unit/
│   ├── test_product_service.py
│   ├── test_order_service.py
│   ├── test_payment_service.py
│   ├── test_pricing_service.py
│   ├── test_validation_service.py
│   ├── test_inventory_service.py
│   └── test_webhook_service.py
├── integration/
│   ├── test_checkout_flow.py
│   ├── test_payment_integration.py
│   ├── test_webhook_delivery.py
│   ├── test_inventory_concurrency.py
│   └── test_cache_integration.py
├── e2e/
│   ├── test_customer_journey.py
│   └── test_admin_workflows.py
├── load/
│   ├── locustfile.py
│   └── test_checkout_load.py
├── security/
│   ├── test_sql_injection.py
│   ├── test_rate_limiting.py
│   └── test_authentication.py
└── conftest.py
```

**Checkout Flow Integration Test:**
```python
# tests/integration/test_checkout_flow.py
import pytest
from decimal import Decimal

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_checkout_flow(
    client,
    db_session,
    sample_product,
    mock_stripe
):
    """Test complete checkout flow from cart to order"""

    # Step 1: Add product to cart
    response = client.post(
        "/api/v1/cart/items",
        json={
            "product_id": str(sample_product.id),
            "quantity": 2,
            "customization_data": {
                "text": "Hello World"
            }
        }
    )
    assert response.status_code == 201
    cart_data = response.json()
    assert len(cart_data["items"]) == 1

    # Step 2: Validate customization
    # (implicit in add to cart)

    # Step 3: Calculate pricing
    assert cart_data["subtotal"] == float(sample_product.base_price * 2)

    # Step 4: Create order
    response = client.post(
        "/api/v1/checkout",
        json={
            "shipping_address": {
                "line1": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94102",
                "country": "US"
            },
            "payment_method": "stripe"
        }
    )
    assert response.status_code == 201
    order_data = response.json()

    # Step 5: Verify order created
    assert order_data["status"] == "created"
    assert order_data["total"] > 0
    order_id = order_data["id"]

    # Step 6: Simulate payment webhook
    response = client.post(
        "/api/v1/webhooks/stripe",
        json=mock_stripe.payment_success_webhook(order_id),
        headers={"stripe-signature": mock_stripe.generate_signature()}
    )
    assert response.status_code == 200

    # Step 7: Verify order paid
    response = client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    order_data = response.json()
    assert order_data["status"] == "paid"

    # Step 8: Verify inventory updated
    # Check inventory was decremented

    # Step 9: Verify webhook sent to fulfillment
    # Check webhook log
```

**Load Testing:**
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class EcommerceUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup for each user"""
        self.session_id = None

    @task(3)
    def browse_products(self):
        """Browse product catalog"""
        self.client.get("/api/v1/products")

    @task(2)
    def view_product(self):
        """View product details"""
        # Assuming we have product IDs
        self.client.get(f"/api/v1/products/{self.product_id}")

    @task(1)
    def add_to_cart(self):
        """Add item to cart"""
        self.client.post(
            "/api/v1/cart/items",
            json={
                "product_id": self.product_id,
                "quantity": 1,
                "customization_data": {}
            }
        )

    @task(0.1)
    def checkout(self):
        """Complete checkout"""
        self.client.post(
            "/api/v1/checkout",
            json={
                "shipping_address": self.shipping_address,
                "payment_method": "stripe"
            }
        )
```

**Mutation Testing:**
```python
# mutation-testing.sh
#!/bin/bash
# Run mutation testing to verify test quality

pip install mutpy

mutpy --target app/services/ --unit-test tests/unit/ \
      --runner pytest --report-html mutation-report/
```

**Coverage Configuration:**
```ini
# .coveragerc
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = coverage_html_report
```

**CI Coverage Check:**
```yaml
# .github/workflows/ci.yml (add)
- name: Check coverage
  run: |
    pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Acceptance Criteria:**
- [ ] Overall coverage > 80%
- [ ] Services coverage > 90%
- [ ] All critical paths tested
- [ ] Integration tests for all workflows
- [ ] Load tests pass 1000 concurrent users
- [ ] Mutation score > 70%
- [ ] CI fails if coverage drops below 80%

---

### Issue #12: API Documentation Enhancement (40% → 100%)
**Status:** 🟡 In Progress
**Priority:** P1 - HIGH
**Estimated Effort:** 1 week
**Assignee:** TBD

**Description:**
Current API docs are auto-generated but lack detailed descriptions, examples, and usage guides.

**Requirements:**
- [ ] Add detailed descriptions to all endpoints
- [ ] Add request/response examples
- [ ] Document error codes
- [ ] Add authentication documentation
- [ ] Create API usage guide
- [ ] Document webhook payloads
- [ ] Add rate limit documentation
- [ ] Create Postman collection

**Files to Create:**
```
docs/
├── api/
│   ├── README.md
│   ├── authentication.md
│   ├── errors.md
│   ├── webhooks.md
│   ├── rate-limiting.md
│   └── pagination.md
├── guides/
│   ├── quick-start.md
│   ├── checkout-flow.md
│   └── customization.md
└── postman/
    └── zerocommerce-collection.json
```

**Enhanced Endpoint Documentation:**
```python
# app/api/v1/endpoints/products.py
@router.post(
    "/",
    response_model=schemas.Product,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="""
    Create a new product in the catalog.

    **Authentication Required:** Yes (Admin API Key)

    **Rate Limit:** 100 requests/hour

    This endpoint allows administrators to add new products to the catalog.
    Products can be customized later by creating associated templates and option sets.

    ### Example Usage

    ```bash
    curl -X POST "https://api.zerocommerce.com/api/v1/products" \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "name": "Custom T-Shirt",
        "description": "100% cotton customizable t-shirt",
        "base_price": 19.99,
        "media": {
          "images": ["https://example.com/shirt.jpg"]
        },
        "is_active": true
      }'
    ```

    ### Business Rules

    - Product name must be unique
    - Base price must be positive
    - Media URLs must be valid HTTPS URLs
    """,
    response_description="The created product with generated ID",
    responses={
        201: {
            "description": "Product created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Custom T-Shirt",
                        "description": "100% cotton customizable t-shirt",
                        "base_price": 19.99,
                        "media": {
                            "images": ["https://example.com/shirt.jpg"]
                        },
                        "is_active": true,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Product name already exists",
                            "details": {
                                "field": "name"
                            },
                            "request_id": "req_123abc"
                        }
                    }
                }
            }
        },
        403: {
            "description": "Invalid or missing API key",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Invalid API key",
                            "request_id": "req_123abc"
                        }
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Retry after 3600 seconds",
                            "details": {
                                "retry_after": 3600
                            },
                            "request_id": "req_123abc"
                        }
                    }
                }
            }
        }
    },
    tags=["Products"]
)
async def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: schemas.ProductCreate,
    api_key: str = Depends(deps.get_admin_key)
) -> Any:
    """Create new product"""
    product = crud.create_product(db=db, product_in=product_in)
    return product
```

**Error Code Documentation:**
```markdown
# docs/api/errors.md

# Error Codes Reference

All errors follow this format:

{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "request_id": "unique-request-id"
  }
}

## Common Error Codes

### Authentication Errors

| Code | Status | Description |
|------|--------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `FORBIDDEN` | 403 | Insufficient permissions |

### Validation Errors

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `REQUIRED_FIELD_MISSING` | 400 | Required field not provided |
| `INVALID_FORMAT` | 400 | Field format is invalid |

### Business Logic Errors

| Code | Status | Description |
|------|--------|-------------|
| `PRODUCT_NOT_FOUND` | 404 | Product does not exist |
| `INSUFFICIENT_STOCK` | 400 | Not enough inventory |
| `PAYMENT_FAILED` | 402 | Payment processing failed |
| `ORDER_ALREADY_PAID` | 400 | Order cannot be modified |

### Rate Limiting

| Code | Status | Description |
|------|--------|-------------|
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |

## Error Handling Best Practices

1. Always check the `code` field for programmatic handling
2. Use `message` for user-facing error messages
3. Log `request_id` for debugging with support
4. Check `details` for additional context
```

**Webhook Documentation:**
```markdown
# docs/api/webhooks.md

# Webhook Events

ZeroCommerce sends webhook events to notify your system of important events.

## Setup

1. Register your webhook endpoint via the admin API
2. Verify webhook signatures to ensure authenticity
3. Return 200 status code within 5 seconds
4. Failed deliveries will be retried up to 5 times

## Event Types

### order.created

Sent when a new order is created.

Payload:
{
  "id": "evt_123",
  "event": "order.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "order_id": "ord_123",
    "order_number": "ORD-2024-001",
    "total": 59.99,
    "items": [...]
  },
  "signature": "..."
}

### order.paid

Sent when payment is confirmed.

### order.shipped

Sent when order is marked as shipped.

## Signature Verification

python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, f"sha256={expected}")
```

**Postman Collection:**
```json
{
  "info": {
    "name": "ZeroCommerce API",
    "description": "Complete API collection for ZeroCommerce",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "apikey",
    "apikey": [
      {
        "key": "key",
        "value": "X-API-Key",
        "type": "string"
      },
      {
        "key": "value",
        "value": "{{API_KEY}}",
        "type": "string"
      }
    ]
  },
  "item": [
    {
      "name": "Products",
      "item": [
        {
          "name": "List Products",
          "request": {
            "method": "GET",
            "url": "{{BASE_URL}}/api/v1/products"
          }
        }
      ]
    }
  ]
}
```

**Acceptance Criteria:**
- [ ] All endpoints have detailed descriptions
- [ ] Request/response examples for all endpoints
- [ ] Error codes documented
- [ ] Webhook documentation complete
- [ ] Postman collection created
- [ ] Quick start guide written
- [ ] Developer feedback incorporated

---

## 🟡 PRIORITY 3: MEDIUM IMPORTANCE

### Issue #13: Monitoring & Observability (5% Complete)
**Status:** ❌ Not Started
**Priority:** P2 - MEDIUM
**Estimated Effort:** 1 week
**Assignee:** TBD

**Description:**
No visibility into production performance. Need comprehensive monitoring setup.

**Requirements:**
- [ ] Add Prometheus metrics endpoint
- [ ] Implement custom business metrics
- [ ] Add Datadog integration
- [ ] Create monitoring dashboards
- [ ] Set up alert rules
- [ ] Add tracing with OpenTelemetry
- [ ] Monitor database performance
- [ ] Track API latencies

**Files to Create:**
```
app/core/metrics.py
app/core/tracing.py
app/middleware/metrics_middleware.py
monitoring/
├── dashboards/
│   ├── api-performance.json
│   ├── business-metrics.json
│   └── system-health.json
├── alerts/
│   ├── critical.yml
│   ├── warning.yml
│   └── info.yml
└── prometheus.yml
```

**Metrics Implementation:**
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# API Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business Metrics
orders_created_total = Counter(
    'orders_created_total',
    'Total orders created',
    ['status']
)

revenue_total = Counter(
    'revenue_total',
    'Total revenue in USD',
    ['payment_method']
)

cart_items_total = Gauge(
    'cart_items_total',
    'Total items in all carts'
)

inventory_level = Gauge(
    'inventory_level',
    'Current inventory level',
    ['product_id']
)

# Payment Metrics
payments_total = Counter(
    'payments_total',
    'Total payments processed',
    ['status', 'provider']
)

payment_duration_seconds = Histogram(
    'payment_duration_seconds',
    'Payment processing duration',
    ['provider']
)

# Webhook Metrics
webhooks_sent_total = Counter(
    'webhooks_sent_total',
    'Total webhooks sent',
    ['event_type', 'status']
)

webhook_delivery_duration_seconds = Histogram(
    'webhook_delivery_duration_seconds',
    'Webhook delivery duration',
    ['event_type']
)

# System Info
app_info = Info(
    'app_info',
    'Application information'
)
app_info.info({
    'version': '0.1.0',
    'environment': 'production'
})

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

**Metrics Middleware:**
```python
# app/middleware/metrics_middleware.py
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response
```

**OpenTelemetry Tracing:**
```python
# app/core/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def setup_tracing(app):
    """Setup OpenTelemetry tracing"""

    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # Set up OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()

    return tracer
```

**Alert Rules:**
```yaml
# monitoring/alerts/critical.yml
groups:
  - name: critical
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/second"

      - alert: PaymentFailureSpike
        expr: rate(payments_total{status="failed"}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Payment failure spike"
          description: "Payment failure rate is {{ $value }}"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API latency"
          description: "P95 latency is {{ $value }}s"
```

**Grafana Dashboard:**
```json
{
  "dashboard": {
    "title": "ZeroCommerce API Performance",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      },
      {
        "title": "Orders Created",
        "targets": [
          {
            "expr": "increase(orders_created_total[1h])"
          }
        ]
      }
    ]
  }
}
```

**Dependencies:**
```txt
prometheus-client>=0.19.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-exporter-otlp>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
opentelemetry-instrumentation-sqlalchemy>=0.42b0
```

**Acceptance Criteria:**
- [ ] `/metrics` endpoint returns Prometheus metrics
- [ ] Business metrics tracked
- [ ] Distributed tracing working
- [ ] Dashboards created in Grafana
- [ ] Alert rules configured
- [ ] Alerts tested in staging
- [ ] Runbook created for alerts

---

### Issue #14: Preview Generation Service (0% Complete)
**Status:** ❌ Not Started
**Priority:** P2 - MEDIUM
**Estimated Effort:** 2-3 weeks
**Assignee:** TBD

**Description:**
Users need to see customized product previews before purchase. Requires async image processing.

**Requirements:**
- [ ] Design preview rendering architecture
- [ ] Integrate image processing library (Pillow)
- [ ] Set up job queue (Celery/RQ)
- [ ] Implement S3 storage integration
- [ ] Build preview API endpoints
- [ ] Add preview caching
- [ ] Handle different product types
- [ ] Add watermark for unpaid previews

**Files to Create:**
```
app/services/preview/
├── __init__.py
├── renderer.py
├── job_queue.py
└── templates/
workers/
├── preview_worker.py
└── celery_config.py
app/api/v1/endpoints/preview.py
tests/unit/test_preview_renderer.py
```

**Architecture:**
```
Client → POST /sessions/{id}/preview
    ↓
API Server → Enqueue job → Redis Queue
    ↓
Return job_id
                            ↓
                      Worker Process
                            ↓
                      Render Image
                            ↓
                      Upload to S3
                            ↓
                      Update job status
Client → GET /previews/{job_id} → Return URL
```

**Preview Service:**
```python
# app/services/preview/renderer.py
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
import boto3
import structlog

logger = structlog.get_logger()

class PreviewRenderer:
    def __init__(
        self,
        s3_bucket: str,
        s3_client: boto3.client
    ):
        self.s3_bucket = s3_bucket
        self.s3_client = s3_client

    async def render_preview(
        self,
        product: Product,
        template: Template,
        customization_data: dict
    ) -> str:
        """
        Render product preview with customizations.

        Returns S3 URL of preview image.
        """
        logger.info(
            "preview_render_started",
            product_id=str(product.id),
            template_id=str(template.id)
        )

        # Load base product image
        base_image = await self._load_base_image(product)

        # Apply customizations
        for zone in template.customization_zones:
            zone_data = customization_data.get(zone.key)
            if not zone_data:
                continue

            if zone.type == "text":
                self._apply_text(base_image, zone, zone_data)
            elif zone.type == "image":
                await self._apply_image(base_image, zone, zone_data)
            elif zone.type == "color":
                self._apply_color(base_image, zone, zone_data)

        # Add watermark for unpaid previews
        self._add_watermark(base_image)

        # Upload to S3
        preview_url = await self._upload_preview(base_image, product.id)

        logger.info(
            "preview_render_completed",
            product_id=str(product.id),
            preview_url=preview_url
        )

        return preview_url

    def _apply_text(
        self,
        image: Image.Image,
        zone: CustomizationZone,
        text: str
    ) -> None:
        """Apply text to image"""
        draw = ImageDraw.Draw(image)

        # Get configuration
        config = zone.config
        position = config.get('position', {'x': 0, 'y': 0})
        font_size = config.get('font_size', 24)
        color = config.get('color', '#000000')

        # Load font
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Draw text
        draw.text(
            (position['x'], position['y']),
            text,
            fill=color,
            font=font
        )
```

**Job Queue:**
```python
# workers/celery_config.py
from celery import Celery

celery_app = Celery(
    'zerocommerce',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
)

# workers/preview_worker.py
from celery import Task
from app.services.preview.renderer import PreviewRenderer

@celery_app.task(bind=True)
def render_preview_task(
    self: Task,
    session_id: str,
    product_id: str,
    template_id: str,
    customization_data: dict
) -> dict:
    """
    Celery task to render preview.

    Returns:
        {
            "status": "completed",
            "preview_url": "https://..."
        }
    """
    try:
        # Get renderer
        renderer = PreviewRenderer(...)

        # Render preview
        preview_url = renderer.render_preview(
            product_id,
            template_id,
            customization_data
        )

        return {
            "status": "completed",
            "preview_url": preview_url
        }

    except Exception as e:
        logger.exception("preview_render_failed", session_id=session_id)
        return {
            "status": "failed",
            "error": str(e)
        }
```

**API Endpoints:**
```python
# app/api/v1/endpoints/preview.py
@router.post("/sessions/{session_id}/preview")
async def request_preview(
    session_id: UUID,
    db: Session = Depends(deps.get_db)
) -> dict:
    """Request preview generation for customization session"""

    # Get session
    session = await crud.get_customization_session(db, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    # Enqueue render job
    task = render_preview_task.delay(
        str(session_id),
        str(session.product_id),
        str(session.template_id),
        session.customization_data
    )

    return {
        "job_id": task.id,
        "status": "processing"
    }

@router.get("/previews/{job_id}")
async def get_preview_status(
    job_id: str
) -> dict:
    """Get preview generation status"""

    task = celery_app.AsyncResult(job_id)

    if task.ready():
        result = task.get()
        return {
            "status": result["status"],
            "preview_url": result.get("preview_url"),
            "error": result.get("error")
        }
    else:
        return {
            "status": "processing",
            "progress": task.info.get("progress", 0)
        }
```

**Dependencies:**
```txt
celery[redis]>=5.3.0
Pillow>=10.1.0
boto3>=1.34.0
```

**Acceptance Criteria:**
- [ ] Preview generation works for text
- [ ] Preview generation works for images
- [ ] Preview generation works for colors
- [ ] Watermark added to unpaid previews
- [ ] Job status trackable via API
- [ ] Failed jobs retry automatically
- [ ] Preview URLs cached
- [ ] Load tested to 100 concurrent renders

---

### Issue #15: Performance Optimization (10% Complete)
**Status:** ❌ Not Started
**Priority:** P2 - MEDIUM
**Estimated Effort:** 1 week
**Assignee:** TBD

**Description:**
Optimize database queries and API performance for production scale.

**Requirements:**
- [ ] Analyze and optimize database queries
- [ ] Add missing database indexes
- [ ] Implement connection pooling
- [ ] Add query result caching
- [ ] Optimize N+1 query patterns
- [ ] Add database query logging
- [ ] Profile slow endpoints
- [ ] Implement pagination everywhere

**Database Index Analysis:**
```sql
-- Add missing indexes from datamodel.md

-- Products
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_products_name ON products(name);

-- Templates
CREATE UNIQUE INDEX idx_template_product_version ON templates(product_id, version);
CREATE UNIQUE INDEX idx_template_default ON templates(product_id) WHERE is_default = TRUE;

-- CustomizationZone
CREATE UNIQUE INDEX idx_zone_template_key ON customization_zones(template_id, key);
CREATE INDEX idx_zone_order ON customization_zones(template_id, order_index);

-- OptionSet
CREATE INDEX idx_optionset_product ON option_sets(product_id);

-- Option
CREATE UNIQUE INDEX idx_option_set_value ON options(option_set_id, value);

-- Inventory
CREATE INDEX idx_inventory_low_stock ON inventory(product_id)
  WHERE (quantity - reserved) <= low_stock_threshold;

-- Orders
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_session ON orders(session_key);

-- WebhookLog
CREATE INDEX idx_webhook_event_type ON webhook_logs(event_type);
CREATE INDEX idx_webhook_sent_at ON webhook_logs(sent_at DESC);
```

**Query Optimization:**
```python
# app/crud/product.py
# BEFORE (N+1 queries)
def get_product_with_templates(db: Session, product_id: UUID):
    product = db.query(Product).filter(Product.id == product_id).first()
    # This triggers N additional queries for templates
    templates = product.templates
    return product

# AFTER (Eager loading)
from sqlalchemy.orm import joinedload, selectinload

def get_product_with_templates(db: Session, product_id: UUID):
    product = db.query(Product).options(
        joinedload(Product.templates).joinedload(Template.customization_zones),
        selectinload(Product.option_sets).selectinload(OptionSet.options)
    ).filter(Product.id == product_id).first()
    return product
```

**Connection Pooling:**
```python
# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Connections to keep open
    max_overflow=0,             # Don't allow overflow
    pool_pre_ping=True,         # Test connections before use
    pool_recycle=3600,          # Recycle connections after 1 hour
    echo=settings.LOG_LEVEL == "DEBUG",  # Log SQL in debug
)
```

**Query Profiling:**
```python
# app/middleware/query_profiler.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import structlog

logger = structlog.get_logger()

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)

    if total > 0.1:  # Log slow queries (>100ms)
        logger.warning(
            "slow_query",
            duration=total,
            statement=statement,
            parameters=parameters
        )
```

**Pagination Helper:**
```python
# app/core/pagination.py
from typing import Generic, TypeVar, List
from pydantic import BaseModel
from math import ceil

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

def paginate(
    query,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse:
    """
    Paginate SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        PaginatedResponse with items and metadata
    """
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    total_pages = ceil(total / page_size)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
```

**Load Testing:**
```bash
# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Performance targets:
# - P50 latency < 100ms
# - P95 latency < 200ms
# - P99 latency < 500ms
# - Support 1000 concurrent users
# - Handle 10,000 requests/minute
```

**Acceptance Criteria:**
- [ ] All indexes from datamodel.md added
- [ ] No N+1 query patterns remaining
- [ ] Connection pooling configured
- [ ] Slow queries logged
- [ ] All list endpoints paginated
- [ ] Load tests pass performance targets
- [ ] Database CPU usage < 60% under load

---

## 🟢 PRIORITY 4: NICE TO HAVE

### Issue #16: Admin & Reporting Endpoints (0% Complete)
**Status:** ❌ Not Started
**Priority:** P3 - LOW
**Estimated Effort:** 1-2 weeks
**Assignee:** TBD

**Description:**
Business intelligence and reporting endpoints for administrators.

**Requirements:**
- [ ] Sales by product report
- [ ] Revenue trends report
- [ ] Popular customizations report
- [ ] Dashboard summary endpoint
- [ ] Export data to CSV/Excel
- [ ] Scheduled report generation

**Files to Create:**
```
app/api/v1/endpoints/reports.py
app/services/reporting.py
app/services/export.py
tests/unit/test_reporting.py
```

**Example Endpoint:**
```python
# app/api/v1/endpoints/reports.py
@router.get("/reports/sales")
async def get_sales_report(
    start_date: date,
    end_date: date,
    group_by: Literal["day", "week", "month"] = "day",
    db: Session = Depends(deps.get_db),
    api_key: str = Depends(deps.get_admin_key)
) -> dict:
    """
    Get sales report for date range.

    Returns revenue, orders, and units sold grouped by time period.
    """
    return await reporting_service.get_sales_report(
        db,
        start_date,
        end_date,
        group_by
    )
```

---

## Implementation Priority Summary

### Week 1-2: Critical Blockers
1. **Order Management** (Issue #1)
2. **Payment Integration** (Issue #2)

### Week 3-4: Security & Infrastructure
3. **Inventory Management** (Issue #3)
4. **Webhook System** (Issue #4)
5. **Security Hardening** (Issue #6)

### Week 5-6: Architecture & Quality
6. **Type Safety** (Issue #5)
7. **Services Layer** (Issue #8)
8. **Error Handling** (Issue #9)

### Week 7-8: Deployment & Stability
9. **Deployment Infrastructure** (Issue #7)
10. **Testing Coverage** (Issue #11)
11. **Redis Caching** (Issue #10)

### Week 9-10: Observability & Performance
12. **Monitoring** (Issue #13)
13. **API Documentation** (Issue #12)
14. **Performance Optimization** (Issue #15)

### Post-Launch
15. **Preview Generation** (Issue #14)
16. **Admin Reporting** (Issue #16)

---

## Success Metrics

- [ ] All P0 issues resolved
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities
- [ ] API response time P95 < 200ms
- [ ] Support 1000 concurrent users
- [ ] 99.9% uptime
- [ ] Zero-downtime deployments working
- [ ] Full monitoring and alerting operational

---

## Notes

- This document should be updated weekly
- Mark issues as completed when merged to main
- Add new issues as discovered
- Update time estimates based on actual progress
- All code changes must include tests
- All PRs require code review
- Production deployments require approval
