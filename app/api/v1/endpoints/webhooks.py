"""
Payment webhook endpoints.

This module handles incoming webhooks from payment providers (Stripe, PayPal)
with signature verification, idempotency, and order status updates.
"""
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.order import PaymentProvider
from app.schemas.order import WebhookProcessingResult
from app.services.webhook_verification import webhook_verification_service
from app.services.order_service import OrderService, OrderStateTransitionError
from app.core.metrics import increment_webhook_failure

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stripe", response_model=WebhookProcessingResult)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(deps.get_db_session)
) -> WebhookProcessingResult:
    """
    Handle Stripe webhook events.

    This endpoint processes payment events from Stripe, including:
    - payment_intent.succeeded: Mark order as paid
    - payment_intent.payment_failed: Mark order as failed
    - payment_intent.canceled: Mark order as cancelled

    Args:
        request: FastAPI request object
        stripe_signature: Stripe signature header for verification
        db: Database session

    Returns:
        Webhook processing result

    Raises:
        HTTPException: If signature verification fails or processing error occurs
    """
    # Get raw request body
    body = await request.body()
    payload_str = body.decode('utf-8')

    # Verify signature
    try:
        webhook_verification_service.verify_stripe_signature(
            payload=payload_str,
            signature_header=stripe_signature
        )
    except Exception:
        # Track signature verification failures
        increment_webhook_failure(provider='stripe', error_type='signature_error')
        raise

    # Parse payload
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as e:
        # Track JSON parsing failures
        increment_webhook_failure(provider='stripe', error_type='parse_error')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(e)}"
        )

    event_id = payload.get('id')
    event_type = payload.get('type')
    event_data = payload.get('data', {}).get('object', {})

    logger.info(f"Processing Stripe webhook: {event_id} ({event_type})")

    # Initialize order service
    order_service = OrderService(db)

    # Check idempotency - has this event been processed?
    if order_service.check_event_processed(event_id):
        logger.info(f"Event {event_id} already processed (idempotent)")
        return WebhookProcessingResult(
            success=True,
            message="Event already processed",
            event_id=event_id,
            processed=True
        )

    # Get payment intent ID
    payment_intent_id = event_data.get('id')
    if not payment_intent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payment intent ID in webhook payload"
        )

    # Find order by payment intent ID
    order = order_service.get_order_by_payment_intent(payment_intent_id)
    if not order:
        logger.warning(f"Order not found for payment intent: {payment_intent_id}")
        # Record event even if order not found
        order_service.record_payment_event(
            order_id=None,
            event_id=event_id,
            event_type=event_type,
            provider=PaymentProvider.STRIPE,
            payload=payload,
            payment_intent_id=payment_intent_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found for payment intent: {payment_intent_id}"
        )

    # Record payment event
    order_service.record_payment_event(
        order_id=order.id,
        event_id=event_id,
        event_type=event_type,
        provider=PaymentProvider.STRIPE,
        payload=payload,
        payment_intent_id=payment_intent_id,
        amount=event_data.get('amount', 0) / 100.0,  # Stripe amounts are in cents
        currency=event_data.get('currency', '').upper()
    )

    try:
        # Handle different event types
        if event_type == 'payment_intent.succeeded':
            order_service.handle_payment_success(
                order=order,
                payment_intent_id=payment_intent_id,
                payment_status='succeeded',
                metadata={'stripe_event_id': event_id}
            )
            logger.info(f"Order {order.id} marked as PAID")

        elif event_type == 'payment_intent.payment_failed':
            error_message = None
            last_error = event_data.get('last_payment_error')
            if last_error:
                error_message = last_error.get('message', 'Payment failed')

            order_service.handle_payment_failure(
                order=order,
                payment_intent_id=payment_intent_id,
                payment_status=event_data.get('status', 'failed'),
                error_message=error_message,
                allow_retry=True
            )
            logger.info(f"Order {order.id} marked as FAILED (retry allowed)")

        elif event_type == 'payment_intent.canceled':
            from app.schemas.order import OrderStatusUpdate
            from app.models.order import OrderStatus

            status_update = OrderStatusUpdate(
                status=OrderStatus.CANCELLED,
                payment_intent_id=payment_intent_id,
                payment_status='canceled'
            )
            order_service.update_order_status(order, status_update)
            logger.info(f"Order {order.id} marked as CANCELLED")

        # Mark event as processed
        order_service.mark_event_processed(event_id, success=True)

        return WebhookProcessingResult(
            success=True,
            message=f"Webhook processed successfully: {event_type}",
            order_id=order.id,
            event_id=event_id,
            processed=True
        )

    except OrderStateTransitionError as e:
        logger.error(f"State transition error for order {order.id}: {str(e)}")
        order_service.mark_event_processed(event_id, success=False, error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing webhook {event_id}: {str(e)}")
        order_service.mark_event_processed(event_id, success=False, error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/paypal", response_model=WebhookProcessingResult)
async def handle_paypal_webhook(
    request: Request,
    db: Session = Depends(deps.get_db_session),
    paypal_transmission_id: str = Header(None, alias="PAYPAL-TRANSMISSION-ID"),
    paypal_transmission_time: str = Header(None, alias="PAYPAL-TRANSMISSION-TIME"),
    paypal_transmission_sig: str = Header(None, alias="PAYPAL-TRANSMISSION-SIG"),
    paypal_cert_url: str = Header(None, alias="PAYPAL-CERT-URL"),
    paypal_auth_algo: str = Header(None, alias="PAYPAL-AUTH-ALGO")
) -> WebhookProcessingResult:
    """
    Handle PayPal webhook events.

    This endpoint processes payment events from PayPal, including:
    - PAYMENT.CAPTURE.COMPLETED: Mark order as paid
    - PAYMENT.CAPTURE.DENIED: Mark order as failed
    - PAYMENT.CAPTURE.REFUNDED: Mark order as refunded

    Args:
        request: FastAPI request object
        db: Database session
        paypal_transmission_id: PayPal transmission ID header
        paypal_transmission_time: PayPal transmission time header
        paypal_transmission_sig: PayPal signature header
        paypal_cert_url: PayPal cert URL header
        paypal_auth_algo: PayPal auth algorithm header

    Returns:
        Webhook processing result

    Raises:
        HTTPException: If signature verification fails or processing error occurs
    """
    # Get request body
    body = await request.body()
    payload_str = body.decode('utf-8')

    # Parse payload
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as e:
        # Track JSON parsing failures
        increment_webhook_failure(provider='paypal', error_type='parse_error')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(e)}"
        )

    # Collect headers for verification
    headers = {
        'PAYPAL-TRANSMISSION-ID': paypal_transmission_id,
        'PAYPAL-TRANSMISSION-TIME': paypal_transmission_time,
        'PAYPAL-TRANSMISSION-SIG': paypal_transmission_sig,
        'PAYPAL-CERT-URL': paypal_cert_url,
        'PAYPAL-AUTH-ALGO': paypal_auth_algo
    }

    # Verify signature
    try:
        webhook_verification_service.verify_paypal_signature(
            payload=payload,
            headers=headers
        )
    except Exception:
        # Track signature verification failures
        increment_webhook_failure(provider='paypal', error_type='signature_error')
        raise

    event_id = payload.get('id')
    event_type = payload.get('event_type')
    resource = payload.get('resource', {})

    logger.info(f"Processing PayPal webhook: {event_id} ({event_type})")

    # Initialize order service
    order_service = OrderService(db)

    # Check idempotency
    if order_service.check_event_processed(event_id):
        logger.info(f"Event {event_id} already processed (idempotent)")
        return WebhookProcessingResult(
            success=True,
            message="Event already processed",
            event_id=event_id,
            processed=True
        )

    # Get payment capture/order ID
    payment_intent_id = resource.get('id')
    if not payment_intent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payment ID in webhook payload"
        )

    # Find order by payment intent ID
    order = order_service.get_order_by_payment_intent(payment_intent_id)
    if not order:
        logger.warning(f"Order not found for PayPal payment: {payment_intent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found for payment: {payment_intent_id}"
        )

    # Extract amount and currency
    amount_data = resource.get('amount', {})
    amount = float(amount_data.get('value', 0))
    currency = amount_data.get('currency_code', 'USD')

    # Record payment event
    order_service.record_payment_event(
        order_id=order.id,
        event_id=event_id,
        event_type=event_type,
        provider=PaymentProvider.PAYPAL,
        payload=payload,
        payment_intent_id=payment_intent_id,
        amount=amount,
        currency=currency
    )

    try:
        # Handle different event types
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            order_service.handle_payment_success(
                order=order,
                payment_intent_id=payment_intent_id,
                payment_status='completed',
                metadata={'paypal_event_id': event_id}
            )
            logger.info(f"Order {order.id} marked as PAID (PayPal)")

        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            order_service.handle_payment_failure(
                order=order,
                payment_intent_id=payment_intent_id,
                payment_status='denied',
                error_message='Payment capture was denied',
                allow_retry=False
            )
            logger.info(f"Order {order.id} marked as FAILED (PayPal)")

        elif event_type == 'PAYMENT.CAPTURE.REFUNDED':
            from app.schemas.order import OrderStatusUpdate
            from app.models.order import OrderStatus

            status_update = OrderStatusUpdate(
                status=OrderStatus.REFUNDED,
                payment_intent_id=payment_intent_id,
                payment_status='refunded'
            )
            order_service.update_order_status(order, status_update)
            logger.info(f"Order {order.id} marked as REFUNDED (PayPal)")

        # Mark event as processed
        order_service.mark_event_processed(event_id, success=True)

        return WebhookProcessingResult(
            success=True,
            message=f"Webhook processed successfully: {event_type}",
            order_id=order.id,
            event_id=event_id,
            processed=True
        )

    except OrderStateTransitionError as e:
        logger.error(f"State transition error for order {order.id}: {str(e)}")
        order_service.mark_event_processed(event_id, success=False, error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing PayPal webhook {event_id}: {str(e)}")
        order_service.mark_event_processed(event_id, success=False, error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )
