"""
Tests for payment webhook endpoints.

Following TDD/BDD principles with describe/it-style test organization.
"""
import hashlib
import hmac
import json
import time
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, PaymentProvider, OrderItem, PaymentEvent
from app.models.product import Product
from app.models.cart import Cart


@pytest.fixture
def sample_product(db_session: Session) -> Product:
    """Create a sample product for testing."""
    product = Product(
        name="Test Product",
        description="A test product",
        base_price=29.99,
        media={"images": ["test.jpg"]},
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_cart(db_session: Session) -> Cart:
    """Create a sample cart for testing."""
    cart = Cart(
        session_id=str(uuid4()),
        user_id=None
    )
    db_session.add(cart)
    db_session.commit()
    db_session.refresh(cart)
    return cart


@pytest.fixture
def sample_order(db_session: Session, sample_product: Product, sample_cart: Cart) -> Order:
    """Create a sample order for testing."""
    order = Order(
        cart_id=sample_cart.id,
        session_id=str(uuid4()),
        customer_email="test@example.com",
        status=OrderStatus.CREATED,
        subtotal=29.99,
        tax=2.40,
        shipping_cost=5.00,
        total=37.39,
        currency="USD",
        shipping_address={
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345",
            "country": "US"
        },
        payment_provider=PaymentProvider.STRIPE,
        payment_intent_id="pi_test_123456"
    )
    db_session.add(order)
    db_session.flush()

    # Add order item
    order_item = OrderItem(
        order_id=order.id,
        product_id=sample_product.id,
        product_name=sample_product.name,
        quantity=1,
        unit_price=29.99,
        total_price=29.99,
        customization_data={}
    )
    db_session.add(order_item)
    db_session.commit()
    db_session.refresh(order)
    return order


# Stripe Webhook Tests
class TestStripeWebhookSignatureVerification:
    """Tests for Stripe webhook signature verification."""

    def test_reject_request_without_signature(self, client: TestClient):
        """Should reject webhook requests without a signature header."""
        payload = {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test_123"}}
        }

        response = client.post(
            "/api/v1/webhooks/stripe",
            json=payload
        )

        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()

    def test_reject_request_with_invalid_signature(self, client: TestClient):
        """Should reject webhook requests with invalid signatures."""
        payload = {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test_123"}}
        }

        response = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": "invalid_signature"}
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_accept_request_with_valid_signature(
        self, client: TestClient, sample_order: Order
    ):
        """Should accept webhook requests with valid Stripe signatures."""
        timestamp = str(int(time.time()))
        payload = {
            "id": "evt_test_valid_123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": sample_order.payment_intent_id,
                    "amount": 3739,
                    "currency": "usd",
                    "status": "succeeded"
                }
            }
        }

        payload_str = json.dumps(payload)
        signed_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            b"test_stripe_webhook_secret",
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        stripe_signature = f"t={timestamp},v1={signature}"

        response = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": stripe_signature}
        )

        assert response.status_code == 200


class TestStripePaymentSuccess:
    """Tests for successful Stripe payment handling."""

    def test_update_order_status_to_paid_on_success(
        self, client: TestClient, db_session: Session, sample_order: Order
    ):
        """Should update order status to 'paid' when payment succeeds."""
        timestamp = str(int(time.time()))
        payload = {
            "id": "evt_success_123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": sample_order.payment_intent_id,
                    "amount": 3739,
                    "currency": "usd",
                    "status": "succeeded"
                }
            }
        }

        payload_str = json.dumps(payload)
        signed_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            b"test_stripe_webhook_secret",
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        stripe_signature = f"t={timestamp},v1={signature}"

        response = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": stripe_signature}
        )

        assert response.status_code == 200

        # Verify order status updated
        db_session.refresh(sample_order)
        assert sample_order.status == OrderStatus.PAID
        assert sample_order.payment_status == "succeeded"
        assert sample_order.paid_at is not None

    def test_record_payment_event_for_audit_trail(
        self, client: TestClient, db_session: Session, sample_order: Order
    ):
        """Should record payment event for audit trail."""
        timestamp = str(int(time.time()))
        event_id = "evt_audit_123"
        payload = {
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": sample_order.payment_intent_id,
                    "amount": 3739,
                    "currency": "usd",
                    "status": "succeeded"
                }
            }
        }

        payload_str = json.dumps(payload)
        signed_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            b"test_stripe_webhook_secret",
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        stripe_signature = f"t={timestamp},v1={signature}"

        response = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": stripe_signature}
        )

        assert response.status_code == 200

        # Verify payment event recorded
        event = db_session.query(PaymentEvent).filter_by(event_id=event_id).first()
        assert event is not None
        assert event.order_id == sample_order.id
        assert event.processed is True
        assert event.provider == PaymentProvider.STRIPE


class TestStripePaymentFailure:
    """Tests for failed Stripe payment handling."""

    def test_update_order_status_to_failed_on_failure(
        self, client: TestClient, db_session: Session, sample_order: Order
    ):
        """Should update order status to 'failed' when payment fails."""
        timestamp = str(int(time.time()))
        payload = {
            "id": "evt_failure_123",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": sample_order.payment_intent_id,
                    "amount": 3739,
                    "currency": "usd",
                    "status": "failed",
                    "last_payment_error": {
                        "code": "card_declined",
                        "message": "Your card was declined."
                    }
                }
            }
        }

        payload_str = json.dumps(payload)
        signed_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            b"test_stripe_webhook_secret",
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        stripe_signature = f"t={timestamp},v1={signature}"

        response = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": stripe_signature}
        )

        assert response.status_code == 200

        # Verify order status updated
        db_session.refresh(sample_order)
        assert sample_order.status == OrderStatus.FAILED
        assert sample_order.payment_status == "failed"

    def test_keep_order_in_created_status_for_retry(
        self, client: TestClient, db_session: Session, sample_order: Order
    ):
        """Should allow retry by keeping order in recoverable state."""
        timestamp = str(int(time.time()))
        payload = {
            "id": "evt_retry_123",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": sample_order.payment_intent_id,
                    "amount": 3739,
                    "currency": "usd",
                    "status": "requires_payment_method"
                }
            }
        }

        payload_str = json.dumps(payload)
        signed_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            b"test_stripe_webhook_secret",
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        stripe_signature = f"t={timestamp},v1={signature}"

        response = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": stripe_signature}
        )

        assert response.status_code == 200

        # Verify order can be retried
        db_session.refresh(sample_order)
        # Order should be in a state that allows retry
        assert sample_order.status in [OrderStatus.CREATED, OrderStatus.FAILED]


class TestWebhookIdempotency:
    """Tests for webhook idempotency handling."""

    def test_process_webhook_event_only_once(
        self, client: TestClient, db_session: Session, sample_order: Order
    ):
        """Should process the same webhook event only once (idempotency)."""
        timestamp = str(int(time.time()))
        event_id = "evt_idempotent_123"
        payload = {
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": sample_order.payment_intent_id,
                    "amount": 3739,
                    "currency": "usd",
                    "status": "succeeded"
                }
            }
        }

        payload_str = json.dumps(payload)
        signed_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            b"test_stripe_webhook_secret",
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        stripe_signature = f"t={timestamp},v1={signature}"

        # First request
        response1 = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": stripe_signature}
        )
        assert response1.status_code == 200

        db_session.refresh(sample_order)
        first_updated_at = sample_order.updated_at

        # Second request with same event ID (should be idempotent)
        response2 = client.post(
            "/api/v1/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": stripe_signature}
        )
        assert response2.status_code == 200

        # Verify event was not processed twice
        db_session.refresh(sample_order)
        events_count = db_session.query(PaymentEvent).filter_by(event_id=event_id).count()
        assert events_count == 1

        # Response should indicate already processed
        assert response2.json()["processed"] is True
