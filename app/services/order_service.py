"""
Order status management service.

This module handles order state transitions with proper validation
and business logic enforcement.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, PaymentEvent
from app.schemas.order import OrderStatusUpdate


class OrderStateTransitionError(Exception):
    """Raised when an invalid order state transition is attempted."""
    pass


class InvalidOrderTransitionError(OrderStateTransitionError):
    """Alias for OrderStateTransitionError for consistency with tests."""
    pass


class OrderService:
    """Service for managing order lifecycle and state transitions."""

    # Define valid state transitions
    VALID_TRANSITIONS = {
        OrderStatus.CREATED: [
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.PAID,
            OrderStatus.FAILED,
            OrderStatus.CANCELLED
        ],
        OrderStatus.PENDING_PAYMENT: [
            OrderStatus.PAID,
            OrderStatus.FAILED,
            OrderStatus.CANCELLED
        ],
        OrderStatus.PAID: [
            OrderStatus.PROCESSING,
            OrderStatus.CANCELLED,
            OrderStatus.REFUNDED
        ],
        OrderStatus.FAILED: [
            OrderStatus.PENDING_PAYMENT,  # Allow retry
            OrderStatus.CANCELLED
        ],
        OrderStatus.PROCESSING: [
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED,
            OrderStatus.REFUNDED
        ],
        OrderStatus.SHIPPED: [
            OrderStatus.DELIVERED,
            OrderStatus.REFUNDED
        ],
        OrderStatus.DELIVERED: [
            OrderStatus.REFUNDED
        ],
        OrderStatus.CANCELLED: [],  # Terminal state
        OrderStatus.REFUNDED: []  # Terminal state
    }

    def __init__(self, db: Session):
        """
        Initialize order service.

        Args:
            db: Database session
        """
        self.db = db

    def get_order_by_payment_intent(
        self,
        payment_intent_id: str
    ) -> Optional[Order]:
        """
        Get order by payment intent ID.

        Args:
            payment_intent_id: Payment intent ID from payment provider

        Returns:
            Order if found, None otherwise
        """
        return self.db.query(Order).filter(
            Order.payment_intent_id == payment_intent_id
        ).first()

    def get_order_by_id(self, order_id: UUID) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order UUID

        Returns:
            Order if found, None otherwise
        """
        return self.db.query(Order).filter(Order.id == order_id).first()

    def can_transition(
        self,
        order_or_status,
        new_status: OrderStatus
    ) -> bool:
        """
        Check if a status transition is valid.

        Args:
            order_or_status: Order instance or OrderStatus enum
            new_status: Desired new status

        Returns:
            True if transition is valid
        """
        # Support both Order instances and OrderStatus enums
        if isinstance(order_or_status, Order):
            current_status = OrderStatus(order_or_status.status)
        else:
            current_status = order_or_status

        if current_status == new_status:
            return True

        valid_next_states = self.VALID_TRANSITIONS.get(current_status, [])
        return new_status in valid_next_states

    def get_allowed_transitions(self, order: Order) -> list:
        """
        Get list of allowed transitions from current order status.

        Args:
            order: Order instance

        Returns:
            List of allowed OrderStatus values
        """
        current_status = OrderStatus(order.status)
        return self.VALID_TRANSITIONS.get(current_status, [])

    def is_terminal_status(self, status: OrderStatus) -> bool:
        """
        Check if a status is terminal (no further transitions allowed).

        Args:
            status: OrderStatus to check

        Returns:
            True if terminal status
        """
        # A status is terminal if it has no valid transitions (except empty list)
        return len(self.VALID_TRANSITIONS.get(status, [])) == 0

    def transition_status(
        self,
        order: Order,
        new_status: OrderStatus,
        commit: bool = True
    ) -> Order:
        """
        Transition order to new status with validation.

        Args:
            order: Order to update
            new_status: New status
            commit: Whether to commit transaction

        Returns:
            Updated order

        Raises:
            InvalidOrderTransitionError: If transition invalid
        """
        if not self.can_transition(order, new_status):
            raise InvalidOrderTransitionError(
                f"Cannot transition order {order.id} from {order.status} to {new_status.value}"
            )

        order.status = new_status.value
        order.updated_at = datetime.utcnow()

        if commit:
            self.db.commit()
            self.db.refresh(order)

        return order

    def mark_as_shipped(
        self,
        order: Order,
        tracking_url: Optional[str],
        commit: bool = True
    ) -> Order:
        """
        Mark order as shipped with tracking URL.

        Args:
            order: Order to update
            tracking_url: Shipping tracking URL
            commit: Whether to commit transaction

        Returns:
            Updated order

        Raises:
            ValueError: If tracking_url not provided
            InvalidOrderTransitionError: If cannot transition to shipped
        """
        if not tracking_url:
            raise ValueError("tracking_url is required when marking order as shipped")

        order = self.transition_status(order, OrderStatus.SHIPPED, commit=False)
        order.tracking_url = tracking_url

        if commit:
            self.db.commit()
            self.db.refresh(order)

        return order

    def mark_as_processing(self, order: Order, commit: bool = True) -> Order:
        """
        Mark order as processing.

        Args:
            order: Order to update
            commit: Whether to commit transaction

        Returns:
            Updated order
        """
        return self.transition_status(order, OrderStatus.PROCESSING, commit=commit)

    def mark_as_delivered(self, order: Order, commit: bool = True) -> Order:
        """
        Mark order as delivered.

        Args:
            order: Order to update
            commit: Whether to commit transaction

        Returns:
            Updated order
        """
        return self.transition_status(order, OrderStatus.DELIVERED, commit=commit)

    def mark_as_paid(
        self,
        order: Order,
        payment_intent_id: str,
        commit: bool = True
    ) -> Order:
        """
        Mark order as paid.

        Args:
            order: Order to update
            payment_intent_id: Payment intent ID
            commit: Whether to commit transaction

        Returns:
            Updated order
        """
        order = self.transition_status(order, OrderStatus.PAID, commit=False)
        order.payment_intent_id = payment_intent_id
        if not order.paid_at:
            order.paid_at = datetime.utcnow()

        if commit:
            self.db.commit()
            self.db.refresh(order)

        return order

    def cancel_order(
        self,
        order: Order,
        reason: Optional[str] = None,
        commit: bool = True
    ) -> Order:
        """
        Cancel an order.

        Args:
            order: Order to cancel
            reason: Optional cancellation reason
            commit: Whether to commit transaction

        Returns:
            Cancelled order
        """
        order = self.transition_status(order, OrderStatus.CANCELLED, commit=False)

        if reason:
            current_notes = order.notes or ""
            order.notes = f"{current_notes}\nCancellation reason: {reason}".strip()

        if commit:
            self.db.commit()
            self.db.refresh(order)

        return order

    def update_order_status(
        self,
        order: Order,
        status_update: OrderStatusUpdate,
        force: bool = False
    ) -> Order:
        """
        Update order status with validation.

        Args:
            order: Order to update
            status_update: Status update data
            force: Skip transition validation (use with caution)

        Returns:
            Updated order

        Raises:
            OrderStateTransitionError: If transition is invalid
        """
        current_status = OrderStatus(order.status)
        new_status = status_update.status

        # Validate transition unless forced
        if not force and not self.can_transition(current_status, new_status):
            raise OrderStateTransitionError(
                f"Invalid status transition from {current_status} to {new_status}"
            )

        # Update order status
        order.status = new_status.value

        # Update payment-related fields
        if status_update.payment_intent_id:
            order.payment_intent_id = status_update.payment_intent_id

        if status_update.payment_status:
            order.payment_status = status_update.payment_status

        # Set paid_at timestamp if transitioning to PAID
        if new_status == OrderStatus.PAID and not order.paid_at:
            order.paid_at = datetime.utcnow()

        # Update metadata if provided
        if status_update.metadata:
            order.metadata = {
                **order.metadata,
                **status_update.metadata
            }

        order.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(order)

        return order

    def handle_payment_success(
        self,
        order: Order,
        payment_intent_id: str,
        payment_status: str = "succeeded",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        Handle successful payment for an order.

        Args:
            order: Order to update
            payment_intent_id: Payment intent ID
            payment_status: Payment status from provider
            metadata: Additional metadata

        Returns:
            Updated order
        """
        status_update = OrderStatusUpdate(
            status=OrderStatus.PAID,
            payment_intent_id=payment_intent_id,
            payment_status=payment_status,
            metadata=metadata or {}
        )

        return self.update_order_status(order, status_update)

    def handle_payment_failure(
        self,
        order: Order,
        payment_intent_id: str,
        payment_status: str = "failed",
        error_message: Optional[str] = None,
        allow_retry: bool = True
    ) -> Order:
        """
        Handle failed payment for an order.

        Args:
            order: Order to update
            payment_intent_id: Payment intent ID
            payment_status: Payment status from provider
            error_message: Error message from provider
            allow_retry: Whether to allow retry (affects status)

        Returns:
            Updated order
        """
        metadata = {}
        if error_message:
            metadata['payment_error'] = error_message

        # If retry is allowed and payment requires a new method, keep in CREATED
        # Otherwise, mark as FAILED
        if allow_retry and payment_status == "requires_payment_method":
            status = OrderStatus.CREATED
        else:
            status = OrderStatus.FAILED

        status_update = OrderStatusUpdate(
            status=status,
            payment_intent_id=payment_intent_id,
            payment_status=payment_status,
            metadata=metadata
        )

        return self.update_order_status(order, status_update)

    def record_payment_event(
        self,
        order_id: UUID,
        event_id: str,
        event_type: str,
        provider: str,
        payload: Dict[str, Any],
        payment_intent_id: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None
    ) -> PaymentEvent:
        """
        Record a payment event for audit trail and idempotency.

        Args:
            order_id: Order ID
            event_id: Unique event ID from provider
            event_type: Type of event
            provider: Payment provider
            payload: Full event payload
            payment_intent_id: Payment intent ID
            amount: Amount (if applicable)
            currency: Currency (if applicable)

        Returns:
            Created payment event
        """
        event = PaymentEvent(
            order_id=order_id,
            event_id=event_id,
            event_type=event_type,
            provider=provider,
            payload=payload,
            payment_intent_id=payment_intent_id,
            amount=amount,
            currency=currency,
            processed=False
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def check_event_processed(self, event_id: str) -> bool:
        """
        Check if an event has already been processed (idempotency check).

        Args:
            event_id: Event ID to check

        Returns:
            True if event was already processed
        """
        event = self.db.query(PaymentEvent).filter(
            PaymentEvent.event_id == event_id
        ).first()

        return event is not None

    def mark_event_processed(
        self,
        event_id: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Mark a payment event as processed.

        Args:
            event_id: Event ID to mark
            success: Whether processing was successful
            error_message: Error message if processing failed
        """
        event = self.db.query(PaymentEvent).filter(
            PaymentEvent.event_id == event_id
        ).first()

        if event:
            event.processed = True
            event.processed_at = datetime.utcnow()
            if error_message:
                event.processing_error = error_message

            self.db.commit()
