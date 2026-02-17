# Payment Webhook Implementation

## Overview

This document describes the implementation of payment webhook handling for Stripe and PayPal payment providers. The implementation follows security best practices, includes idempotency handling, and manages order state transitions with a proper state machine.

## Architecture

### Components

1. **Models** (`app/models/order.py`)
   - `Order`: Main order model with status tracking
   - `OrderItem`: Individual items in an order
   - `PaymentEvent`: Audit trail for webhook events (idempotency)
   - `OrderStatus`: Enum defining order statuses
   - `PaymentProvider`: Enum for supported payment providers

2. **Services**
   - `WebhookVerificationService` (`app/services/webhook_verification.py`): Verifies webhook signatures
   - `OrderService` (`app/services/order_service.py`): Manages order state transitions

3. **Endpoints** (`app/api/v1/endpoints/webhooks.py`)
   - `POST /api/v1/webhooks/stripe`: Stripe webhook handler
   - `POST /api/v1/webhooks/paypal`: PayPal webhook handler

4. **Schemas** (`app/schemas/order.py`)
   - Request/response schemas for orders and webhook events
   - Validation for webhook payloads

## Order State Machine

```
CREATED -> PENDING_PAYMENT -> PAID -> PROCESSING -> SHIPPED -> DELIVERED
   |            |              |          |            |
   |            |              |          |            v
   |            |              |          |         REFUNDED
   |            |              |          |
   |            |              |          v
   |            |              |      CANCELLED
   |            |              |
   |            |              v
   |            |          REFUNDED
   |            |
   |            v
   |        FAILED -> (retry) -> PENDING_PAYMENT
   |            |
   |            v
   |        CANCELLED
   |
   v
CANCELLED
```

### Valid State Transitions

- `CREATED`: Can transition to PENDING_PAYMENT, PAID, FAILED, or CANCELLED
- `PENDING_PAYMENT`: Can transition to PAID, FAILED, or CANCELLED
- `PAID`: Can transition to PROCESSING, CANCELLED, or REFUNDED
- `FAILED`: Can retry (transition back to PENDING_PAYMENT) or be CANCELLED
- Terminal states: CANCELLED, REFUNDED, DELIVERED

## Security

### Webhook Signature Verification

#### Stripe
- Uses HMAC SHA-256 signature verification
- Validates timestamp to prevent replay attacks (300-second tolerance)
- Requires `Stripe-Signature` header with format: `t=<timestamp>,v1=<signature>`

#### PayPal
- Validates required headers:
  - `PAYPAL-TRANSMISSION-ID`
  - `PAYPAL-TRANSMISSION-TIME`
  - `PAYPAL-TRANSMISSION-SIG`
  - `PAYPAL-CERT-URL`
  - `PAYPAL-AUTH-ALGO`
- In production, uses PayPal SDK for full signature verification

### Configuration

Add to `.env`:
```env
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret
PAYPAL_WEBHOOK_ID=your_paypal_webhook_id
```

## Idempotency

The system ensures webhook events are processed exactly once:

1. Each webhook event has a unique `event_id`
2. `PaymentEvent` model stores processed events
3. Before processing, system checks if `event_id` exists
4. If event already processed, returns success without reprocessing
5. Prevents duplicate order status updates

## Retry Logic

### Failed Payments

When a payment fails:
- If `status` is `requires_payment_method`: Order remains in `CREATED` status (allows retry)
- If `status` is `failed`: Order transitions to `FAILED` status
- Error messages stored in order metadata for debugging

### Webhook Retry (Provider Side)

Providers automatically retry webhook delivery:
- **Stripe**: Retries up to 3 days with exponential backoff
- **PayPal**: Configurable retry schedule (typically 24 hours)

System returns appropriate HTTP status codes:
- `200 OK`: Event processed successfully (or already processed)
- `400 Bad Request`: Invalid signature or payload
- `404 Not Found`: Order not found
- `500 Internal Server Error`: Processing error (will be retried)

## Supported Webhook Events

### Stripe

| Event Type | Action |
|------------|--------|
| `payment_intent.succeeded` | Update order to PAID, set `paid_at` timestamp |
| `payment_intent.payment_failed` | Update order to FAILED or keep in CREATED for retry |
| `payment_intent.canceled` | Update order to CANCELLED |
| `charge.succeeded` | Alternative success event |
| `charge.failed` | Alternative failure event |
| `charge.refunded` | Update order to REFUNDED |

### PayPal

| Event Type | Action |
|------------|--------|
| `PAYMENT.CAPTURE.COMPLETED` | Update order to PAID |
| `PAYMENT.CAPTURE.DENIED` | Update order to FAILED |
| `PAYMENT.CAPTURE.REFUNDED` | Update order to REFUNDED |
| `CHECKOUT.ORDER.APPROVED` | Update order to PENDING_PAYMENT |
| `CHECKOUT.ORDER.COMPLETED` | Update order to PAID |

## Testing

### Test Structure

Tests follow BDD (Behavior-Driven Development) principles:
- Organized by feature (`describe_*` style grouping)
- Clear test names describing behavior (`it_should_*`)
- Comprehensive coverage of success, failure, and edge cases

### Test Files

- `tests/api/test_webhooks.py`: BDD-style tests (describe/it format)
- `tests/api/test_webhooks_simple.py`: Pytest-style tests

### Running Tests

```bash
# Run webhook tests
pytest tests/api/test_webhooks_simple.py -v

# Run with coverage
pytest tests/api/test_webhooks_simple.py --cov=app.services --cov=app.api.v1.endpoints.webhooks -v

# Run all tests
pytest --cov=app --cov-report=html
```

### Test Scenarios Covered

1. **Signature Verification**
   - ✓ Reject requests without signature
   - ✓ Reject requests with invalid signature
   - ✓ Accept requests with valid signature

2. **Payment Success**
   - ✓ Update order status to PAID
   - ✓ Set paid_at timestamp
   - ✓ Record payment event for audit

3. **Payment Failure**
   - ✓ Update order status to FAILED
   - ✓ Keep order in CREATED for retry scenarios
   - ✓ Store error messages

4. **Idempotency**
   - ✓ Process event only once
   - ✓ Return success for duplicate events
   - ✓ Prevent duplicate order updates

5. **State Transitions**
   - ✓ Validate all transitions
   - ✓ Reject invalid transitions
   - ✓ Allow retry from FAILED to PENDING_PAYMENT

## Usage Examples

### Stripe Webhook Setup

1. In Stripe Dashboard, configure webhook endpoint:
   ```
   https://your-domain.com/api/v1/webhooks/stripe
   ```

2. Select events to send:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `payment_intent.canceled`

3. Copy webhook signing secret to `.env`:
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

### PayPal Webhook Setup

1. In PayPal Developer Dashboard, create webhook:
   ```
   https://your-domain.com/api/v1/webhooks/paypal
   ```

2. Select event types:
   - `PAYMENT.CAPTURE.COMPLETED`
   - `PAYMENT.CAPTURE.DENIED`
   - `PAYMENT.CAPTURE.REFUNDED`

3. Copy webhook ID to `.env`:
   ```env
   PAYPAL_WEBHOOK_ID=...
   ```

## Monitoring and Logging

### Logged Events

- Webhook receipt and processing start
- Signature verification results
- Order status transitions
- Idempotency checks
- Processing errors

### Metrics to Monitor

1. **Webhook Processing Rate**: Events processed per minute
2. **Processing Time**: Average time to process webhooks
3. **Error Rate**: Failed webhook processing attempts
4. **Idempotent Requests**: Duplicate event detection rate
5. **State Transition Errors**: Invalid transitions attempted

### Example Log Output

```
INFO: Processing Stripe webhook: evt_1234 (payment_intent.succeeded)
INFO: Order 550e8400-e29b-41d4-a716-446655440000 marked as PAID
INFO: Event evt_1234 processed successfully
```

## Error Handling

### Common Errors

1. **Invalid Signature**
   - HTTP 400
   - Message: "Invalid Stripe/PayPal signature"
   - Action: Check webhook secret configuration

2. **Order Not Found**
   - HTTP 404
   - Message: "Order not found for payment intent: ..."
   - Action: Verify payment_intent_id matches order

3. **Invalid State Transition**
   - HTTP 400
   - Message: "Invalid status transition from X to Y"
   - Action: Review state machine logic

4. **Duplicate Event**
   - HTTP 200 (Success)
   - Message: "Event already processed"
   - Action: None (expected behavior)

## Future Enhancements

1. **Additional Payment Providers**: Implement Square, Apple Pay, Google Pay
2. **Async Processing**: Use Celery for webhook processing
3. **Enhanced Monitoring**: Add Datadog/Sentry integration
4. **Webhook Testing UI**: Admin panel for testing webhook handling
5. **Automated Retry**: Implement client-side retry for failed webhooks
6. **Multi-currency Support**: Enhanced currency conversion handling
7. **Fraud Detection**: Integration with fraud detection services

## Related Documentation

- [Order API Documentation](./ORDER_API.md)
- [Security Best Practices](./SECURITY.md)
- [Deployment Guide](./deployment/PRODUCTION_READINESS.md)
- [Testing Strategy](./TESTING.md)

## Support

For issues or questions:
1. Check logs for error details
2. Verify webhook configuration in provider dashboard
3. Test webhook delivery using provider's testing tools
4. Review PaymentEvent records for audit trail
