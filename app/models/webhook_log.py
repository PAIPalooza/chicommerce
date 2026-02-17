"""WebhookLog model for auditing webhook deliveries."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class WebhookLog(Base):
    """
    WebhookLog model for auditing webhook delivery attempts.

    This model tracks all webhook delivery attempts including the event type,
    payload, response status, and timing information for troubleshooting
    delivery failures.
    """
    __tablename__ = "webhook_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)

    # Event information
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Webhook delivery details
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), default="POST", nullable=False)

    # Request payload
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Response information
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timing information
    sent_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False, index=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Retry information
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_success: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_webhook_log_event_type_sent_at', 'event_type', 'sent_at'),
        Index('idx_webhook_log_status_sent_at', 'response_status', 'sent_at'),
        Index('idx_webhook_log_success_sent_at', 'is_success', 'sent_at'),
    )

    def __repr__(self) -> str:
        return f"<WebhookLog {self.id} event={self.event_type} status={self.response_status}>"
