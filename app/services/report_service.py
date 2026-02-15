"""
Report service for generating sales and analytics reports.

This module provides efficient SQL-based report generation with proper
aggregation and filtering capabilities for admin analytics.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, cast, Integer
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSONB

from app.models import Order, OrderItem, Product


@dataclass
class SalesReportItem:
    """
    Data class representing a single row in the sales report.

    Aggregates sales data by product_id and template_version.
    """
    product_id: UUID
    product_name: str
    template_version: Optional[int]
    total_quantity: int
    total_revenue: Decimal
    order_count: int

    def to_dict(self) -> dict:
        """
        Convert SalesReportItem to dictionary for API response.

        Returns:
            Dictionary representation with string-formatted values
        """
        return {
            "product_id": str(self.product_id),
            "product_name": self.product_name,
            "template_version": self.template_version,
            "total_quantity": self.total_quantity,
            "total_revenue": str(self.total_revenue),
            "order_count": self.order_count
        }


class ReportService:
    """
    Service for generating various reports from order data.

    Implements optimized SQL queries for report generation with proper
    indexing utilization and efficient aggregation.
    """

    def __init__(self, db: Session):
        """
        Initialize ReportService with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def generate_sales_report(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SalesReportItem]:
        """
        Generate sales report grouped by product_id and template_version.

        This method executes an optimized SQL query that:
        - Filters orders by date range and paid status
        - Joins with order_items and products for complete data
        - Extracts template_version from JSONB customization_data
        - Groups by product_id and template_version
        - Aggregates quantity, revenue, and order count
        - Supports pagination for large result sets

        Args:
            start_date: Start date for report (inclusive). Defaults to 30 days ago.
            end_date: End date for report (inclusive). Defaults to today.
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            List of SalesReportItem objects with aggregated sales data

        Note:
            - Only includes orders with status='paid'
            - Uses database indexes on order.status, order.paid_at, and order_items.product_id
            - Template version is extracted from order_items.customization_data->>'template_version'
        """
        # Default date range: last 30 days
        if end_date is None:
            end_date = datetime.utcnow().date()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Build the query with efficient joins and aggregation
        # Extract template_version from JSON using ->> operator
        # This returns text which we'll convert to int later
        template_version_expr = cast(
            OrderItem.customization_data.op('->>')('template_version'),
            Integer
        )

        query = (
            self.db.query(
                OrderItem.product_id,
                Product.name.label('product_name'),
                template_version_expr.label('template_version'),
                func.sum(OrderItem.quantity).label('total_quantity'),
                func.sum(OrderItem.total_price).label('total_revenue'),
                func.count(func.distinct(Order.id)).label('order_count')
            )
            .join(Order, OrderItem.order_id == Order.id)
            .join(Product, OrderItem.product_id == Product.id)
            .filter(
                Order.status == 'paid',
                func.date(Order.paid_at) >= start_date,
                func.date(Order.paid_at) <= end_date
            )
            .group_by(
                OrderItem.product_id,
                Product.name,
                template_version_expr
            )
            .order_by(
                func.sum(OrderItem.total_price).desc()  # Order by revenue descending
            )
            .offset(skip)
            .limit(limit)
        )

        # Execute query and convert to SalesReportItem objects
        results = query.all()

        sales_items = []
        for row in results:
            item = SalesReportItem(
                product_id=row.product_id,
                product_name=row.product_name,
                template_version=row.template_version,  # Already cast to Integer or NULL
                total_quantity=int(row.total_quantity or 0),
                total_revenue=Decimal(str(row.total_revenue or 0)),
                order_count=int(row.order_count or 0)
            )
            sales_items.append(item)

        return sales_items
