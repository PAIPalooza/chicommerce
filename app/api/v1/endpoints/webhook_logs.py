"""
Webhook logs audit endpoint.

This module provides endpoints for auditing webhook delivery attempts,
allowing administrators to troubleshoot delivery failures and monitor
webhook performance.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.models.webhook_log import WebhookLog
from app.schemas.webhook_log import WebhookLogListResponse, WebhookLogResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=WebhookLogListResponse)
def get_webhook_logs(
    event: Optional[str] = Query(None, description="Filter by event type (e.g., 'order.created')"),
    status: Optional[int] = Query(None, ge=100, le=599, description="Filter by HTTP response status code"),
    success: Optional[bool] = Query(None, description="Filter by success/failure status"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return (max 100)"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(deps.get_db_session),
    api_key: str = Depends(deps.get_admin_key)
) -> WebhookLogListResponse:
    """
    Retrieve webhook logs with optional filtering and pagination.

    This endpoint allows administrators to audit webhook delivery attempts,
    troubleshoot failures, and monitor webhook performance. It supports
    filtering by event type, response status, and success status.

    Args:
        event: Filter logs by event type (e.g., 'order.created')
        status: Filter logs by HTTP response status code (100-599)
        success: Filter logs by success status (true/false)
        limit: Maximum number of logs to return (1-100, default: 50)
        offset: Number of logs to skip for pagination (default: 0)
        db: Database session (injected)
        api_key: Admin API key for authentication (injected)

    Returns:
        Paginated list of webhook logs with metadata

    Raises:
        HTTPException: 401 if API key is missing, 403 if API key is invalid

    Example:
        GET /api/v1/webhooklogs?event=order.created&limit=20&offset=0
    """
    # Build query
    query = db.query(WebhookLog)

    # Apply filters
    if event:
        query = query.filter(WebhookLog.event_type == event)

    if status is not None:
        query = query.filter(WebhookLog.response_status == status)

    if success is not None:
        query = query.filter(WebhookLog.is_success == success)

    # Get total count before pagination
    total = query.count()

    # Apply sorting (newest first)
    query = query.order_by(desc(WebhookLog.sent_at))

    # Apply pagination
    logs = query.limit(limit).offset(offset).all()

    # Determine if there are more results
    has_more = (offset + limit) < total

    # Convert to response models
    log_responses = [WebhookLogResponse.model_validate(log) for log in logs]

    logger.info(
        f"Retrieved {len(logs)} webhook logs (total: {total}, filters: event={event}, "
        f"status={status}, success={success}, limit={limit}, offset={offset})"
    )

    return WebhookLogListResponse(
        items=log_responses,
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more
    )
