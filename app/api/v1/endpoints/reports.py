"""
Report API endpoints for admin analytics.

Provides endpoints for generating sales reports and analytics data.
All endpoints require admin authentication via API key.
"""
from datetime import date, datetime, timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/sales", response_model=List[schemas.SalesReportItemResponse])
async def get_sales_report(
    *,
    db: Session = Depends(deps.get_db_session),
    api_key: str = Depends(deps.get_admin_key),
    start: date | None = Query(
        None,
        description="Start date for report (inclusive). Defaults to 30 days ago."
    ),
    end: date | None = Query(
        None,
        description="End date for report (inclusive). Defaults to today."
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip for pagination"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return (max 1000)"
    )
) -> Any:
    """
    Retrieve sales report grouped by product_id and template_version.

    This endpoint generates aggregated sales data for admin analytics:
    - Groups sales by product and template version
    - Aggregates total quantity, revenue, and order count
    - Filters by date range (defaults to last 30 days)
    - Only includes orders with 'paid' status
    - Supports pagination for large result sets

    Query Parameters:
        start: Start date for report (YYYY-MM-DD). Defaults to 30 days ago.
        end: End date for report (YYYY-MM-DD). Defaults to today.
        skip: Number of records to skip for pagination (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)

    Returns:
        List of sales report items, each containing:
        - product_id: UUID of the product
        - product_name: Name of the product
        - template_version: Template version used (or null)
        - total_quantity: Total items sold
        - total_revenue: Total revenue generated
        - order_count: Number of unique orders

    Authentication:
        Requires valid admin API key in X-API-Key header

    Example:
        GET /api/v1/reports/sales?start=2024-01-01&end=2024-01-31&limit=50
    """
    # Validate date range
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )

    # Initialize report service
    report_service = ReportService(db)

    # Generate sales report
    sales_data = report_service.generate_sales_report(
        start_date=start,
        end_date=end,
        skip=skip,
        limit=limit
    )

    # Convert to response models
    response = [
        schemas.SalesReportItemResponse(
            product_id=item.product_id,
            product_name=item.product_name,
            template_version=item.template_version,
            total_quantity=item.total_quantity,
            total_revenue=item.total_revenue,
            order_count=item.order_count
        )
        for item in sales_data
    ]

    return response
