"""
Unit tests for report service.

Following TDD/BDD approach with descriptive test names for clear test organization.
Tests written BEFORE implementation to ensure proper test-driven development.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.report_service import ReportService, SalesReportItem


class TestReportService:
    """Test suite for ReportService sales report generation."""

    def test_generate_sales_report_with_date_range(self, db_session):
        """Should generate sales report grouped by product_id and template version for date range."""
        # Create test data
        from app.models import Product, Template, Order, OrderItem, Cart

        # Create products
        product1 = Product(
            name="T-Shirt",
            description="Test T-Shirt",
            base_price=Decimal("19.99"),
            is_active=True
        )
        product2 = Product(
            name="Mug",
            description="Test Mug",
            base_price=Decimal("9.99"),
            is_active=True
        )
        db_session.add_all([product1, product2])
        db_session.flush()

        # Create templates
        template1_v1 = Template(
            product_id=product1.id,
            version=1,
            definition={"zones": {}},
            is_default=True
        )
        template1_v2 = Template(
            product_id=product1.id,
            version=2,
            definition={"zones": {}},
            is_default=False
        )
        template2_v1 = Template(
            product_id=product2.id,
            version=1,
            definition={"zones": {}},
            is_default=True
        )
        db_session.add_all([template1_v1, template1_v2, template2_v1])
        db_session.flush()

        # Create carts
        cart1 = Cart(session_id="session1")
        cart2 = Cart(session_id="session2")
        db_session.add_all([cart1, cart2])
        db_session.flush()

        # Create orders from the past 7 days
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)

        order1 = Order(
            cart_id=cart1.id,
            session_id="session1",
            status="paid",
            subtotal=Decimal("39.98"),
            tax=Decimal("4.00"),
            shipping_cost=Decimal("8.99"),
            total=Decimal("52.97"),
            currency="USD",
            shipping_address={"street": "123 Main St"},
            customer_email="test1@example.com",
            created_at=yesterday,
            paid_at=yesterday
        )
        order2 = Order(
            cart_id=cart2.id,
            session_id="session2",
            status="paid",
            subtotal=Decimal("19.99"),
            tax=Decimal("2.00"),
            shipping_cost=Decimal("8.99"),
            total=Decimal("30.98"),
            currency="USD",
            shipping_address={"street": "456 Oak Ave"},
            customer_email="test2@example.com",
            created_at=today,
            paid_at=today
        )
        db_session.add_all([order1, order2])
        db_session.flush()

        # Create order items with customization_data including template_version
        order1_item1 = OrderItem(
            order_id=order1.id,
            product_id=product1.id,
            product_name="T-Shirt",
            quantity=2,
            unit_price=Decimal("19.99"),
            total_price=Decimal("39.98"),
            customization_data={"template_version": 1}
        )
        order2_item1 = OrderItem(
            order_id=order2.id,
            product_id=product1.id,
            product_name="T-Shirt",
            quantity=1,
            unit_price=Decimal("19.99"),
            total_price=Decimal("19.99"),
            customization_data={"template_version": 2}
        )
        db_session.add_all([order1_item1, order2_item1])
        db_session.commit()

        # Test the service
        report_service = ReportService(db_session)
        start_date = yesterday.date()
        end_date = today.date()

        result = report_service.generate_sales_report(
            start_date=start_date,
            end_date=end_date
        )

        # Verify results
        assert len(result) == 2

        # Find the items in results (order may vary)
        product1_v1_item = next((r for r in result if r.product_id == product1.id and r.template_version == 1), None)
        product1_v2_item = next((r for r in result if r.product_id == product1.id and r.template_version == 2), None)

        assert product1_v1_item is not None
        assert product1_v1_item.product_name == "T-Shirt"
        assert product1_v1_item.total_quantity == 2
        assert product1_v1_item.total_revenue == Decimal("39.98")
        assert product1_v1_item.order_count == 1

        assert product1_v2_item is not None
        assert product1_v2_item.product_name == "T-Shirt"
        assert product1_v2_item.total_quantity == 1
        assert product1_v2_item.total_revenue == Decimal("19.99")
        assert product1_v2_item.order_count == 1

    def test_generate_sales_report_filters_by_date(self, db_session):
        """Should only include orders within the specified date range."""
        from app.models import Product, Order, OrderItem, Cart

        product = Product(
            name="Test Product",
            base_price=Decimal("10.00"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        # Create carts
        old_cart = Cart(session_id="old")
        recent_cart = Cart(session_id="recent")
        db_session.add_all([old_cart, recent_cart])
        db_session.flush()

        # Create orders at different dates
        old_date = datetime.utcnow() - timedelta(days=30)
        recent_date = datetime.utcnow() - timedelta(days=1)

        old_order = Order(
            cart_id=old_cart.id,
            session_id="old",
            status="paid",
            subtotal=Decimal("10.00"),
            tax=Decimal("1.00"),
            shipping_cost=Decimal("5.00"),
            total=Decimal("16.00"),
            currency="USD",
            shipping_address={},
            customer_email="old@example.com",
            created_at=old_date,
            paid_at=old_date
        )
        recent_order = Order(
            cart_id=recent_cart.id,
            session_id="recent",
            status="paid",
            subtotal=Decimal("10.00"),
            tax=Decimal("1.00"),
            shipping_cost=Decimal("5.00"),
            total=Decimal("16.00"),
            currency="USD",
            shipping_address={},
            customer_email="recent@example.com",
            created_at=recent_date,
            paid_at=recent_date
        )
        db_session.add_all([old_order, recent_order])
        db_session.flush()

        old_item = OrderItem(
            order_id=old_order.id,
            product_id=product.id,
            product_name="Test Product",
            quantity=1,
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
            customization_data={"template_version": 1}
        )
        recent_item = OrderItem(
            order_id=recent_order.id,
            product_id=product.id,
            product_name="Test Product",
            quantity=1,
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
            customization_data={"template_version": 1}
        )
        db_session.add_all([old_item, recent_item])
        db_session.commit()

        report_service = ReportService(db_session)

        # Query only recent week
        start_date = (datetime.utcnow() - timedelta(days=7)).date()
        end_date = datetime.utcnow().date()

        result = report_service.generate_sales_report(
            start_date=start_date,
            end_date=end_date
        )

        # Should only include recent order
        assert len(result) == 1
        assert result[0].total_quantity == 1
        assert result[0].order_count == 1

    def test_generate_sales_report_only_includes_paid_orders(self, db_session):
        """Should only include orders with 'paid' status."""
        from app.models import Product, Order, OrderItem, Cart

        product = Product(
            name="Test Product",
            base_price=Decimal("10.00"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        # Create carts
        paid_cart = Cart(session_id="paid")
        pending_cart = Cart(session_id="pending")
        db_session.add_all([paid_cart, pending_cart])
        db_session.flush()

        today = datetime.utcnow()

        # Create orders with different statuses
        paid_order = Order(
            cart_id=paid_cart.id,
            session_id="paid",
            status="paid",
            subtotal=Decimal("10.00"),
            tax=Decimal("1.00"),
            shipping_cost=Decimal("5.00"),
            total=Decimal("16.00"),
            currency="USD",
            shipping_address={},
            customer_email="paid@example.com",
            created_at=today,
            paid_at=today
        )
        pending_order = Order(
            cart_id=pending_cart.id,
            session_id="pending",
            status="pending_payment",
            subtotal=Decimal("10.00"),
            tax=Decimal("1.00"),
            shipping_cost=Decimal("5.00"),
            total=Decimal("16.00"),
            currency="USD",
            shipping_address={},
            customer_email="pending@example.com",
            created_at=today
        )
        db_session.add_all([paid_order, pending_order])
        db_session.flush()

        paid_item = OrderItem(
            order_id=paid_order.id,
            product_id=product.id,
            product_name="Test Product",
            quantity=1,
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
            customization_data={"template_version": 1}
        )
        pending_item = OrderItem(
            order_id=pending_order.id,
            product_id=product.id,
            product_name="Test Product",
            quantity=1,
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
            customization_data={"template_version": 1}
        )
        db_session.add_all([paid_item, pending_item])
        db_session.commit()

        report_service = ReportService(db_session)
        result = report_service.generate_sales_report(
            start_date=today.date(),
            end_date=today.date()
        )

        # Should only include paid order
        assert len(result) == 1
        assert result[0].order_count == 1

    def test_generate_sales_report_handles_empty_results(self, db_session):
        """Should return empty list when no orders match criteria."""
        report_service = ReportService(db_session)

        # Query future dates
        start_date = (datetime.utcnow() + timedelta(days=1)).date()
        end_date = (datetime.utcnow() + timedelta(days=7)).date()

        result = report_service.generate_sales_report(
            start_date=start_date,
            end_date=end_date
        )

        assert result == []

    def test_generate_sales_report_aggregates_multiple_orders(self, db_session):
        """Should correctly aggregate multiple orders for same product/template."""
        from app.models import Product, Order, OrderItem, Cart

        product = Product(
            name="Popular Product",
            base_price=Decimal("15.00"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        # Create carts
        carts = [Cart(session_id=f"session{i}") for i in range(3)]
        db_session.add_all(carts)
        db_session.flush()

        today = datetime.utcnow()

        # Create multiple orders for same product/template
        orders = []
        for i in range(3):
            order = Order(
                cart_id=carts[i].id,
                session_id=f"session{i}",
                status="paid",
                subtotal=Decimal("15.00") * (i + 1),
                tax=Decimal("1.50") * (i + 1),
                shipping_cost=Decimal("5.00"),
                total=Decimal("21.50") * (i + 1),
                currency="USD",
                shipping_address={},
                customer_email=f"test{i}@example.com",
                created_at=today,
                paid_at=today
            )
            orders.append(order)

        db_session.add_all(orders)
        db_session.flush()

        # Create order items
        items = []
        for i, order in enumerate(orders):
            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name="Popular Product",
                quantity=i + 1,
                unit_price=Decimal("15.00"),
                total_price=Decimal("15.00") * (i + 1),
                customization_data={"template_version": 1}
            )
            items.append(item)

        db_session.add_all(items)
        db_session.commit()

        report_service = ReportService(db_session)
        result = report_service.generate_sales_report(
            start_date=today.date(),
            end_date=today.date()
        )

        assert len(result) == 1
        assert result[0].total_quantity == 6  # 1 + 2 + 3
        assert result[0].total_revenue == Decimal("90.00")  # 15 + 30 + 45
        assert result[0].order_count == 3

    def test_generate_sales_report_with_pagination(self, db_session):
        """Should support pagination for large result sets."""
        from app.models import Product, Order, OrderItem, Cart

        # Create multiple products
        products = []
        for i in range(10):
            product = Product(
                name=f"Product {i}",
                base_price=Decimal("10.00"),
                is_active=True
            )
            products.append(product)

        db_session.add_all(products)
        db_session.flush()

        # Create carts
        carts = [Cart(session_id=f"session_{i}") for i in range(10)]
        db_session.add_all(carts)
        db_session.flush()

        today = datetime.utcnow()

        # Create order for each product
        for i, product in enumerate(products):
            order = Order(
                cart_id=carts[i].id,
                session_id=f"session_{product.id}",
                status="paid",
                subtotal=Decimal("10.00"),
                tax=Decimal("1.00"),
                shipping_cost=Decimal("5.00"),
                total=Decimal("16.00"),
                currency="USD",
                shipping_address={},
                customer_email=f"{product.id}@example.com",
                created_at=today,
                paid_at=today
            )
            db_session.add(order)
            db_session.flush()

            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=1,
                unit_price=Decimal("10.00"),
                total_price=Decimal("10.00"),
                customization_data={"template_version": 1}
            )
            db_session.add(item)

        db_session.commit()

        report_service = ReportService(db_session)

        # Test pagination
        page1 = report_service.generate_sales_report(
            start_date=today.date(),
            end_date=today.date(),
            skip=0,
            limit=5
        )
        page2 = report_service.generate_sales_report(
            start_date=today.date(),
            end_date=today.date(),
            skip=5,
            limit=5
        )

        assert len(page1) == 5
        assert len(page2) == 5

        # Ensure different results
        page1_ids = {(r.product_id, r.template_version) for r in page1}
        page2_ids = {(r.product_id, r.template_version) for r in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_generate_sales_report_handles_missing_template_version(self, db_session):
        """Should handle order items without template_version in customization_data."""
        from app.models import Product, Order, OrderItem, Cart

        product = Product(
            name="Test Product",
            base_price=Decimal("10.00"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        # Create cart
        cart = Cart(session_id="session")
        db_session.add(cart)
        db_session.flush()

        today = datetime.utcnow()

        order = Order(
            cart_id=cart.id,
            session_id="session",
            status="paid",
            subtotal=Decimal("10.00"),
            tax=Decimal("1.00"),
            shipping_cost=Decimal("5.00"),
            total=Decimal("16.00"),
            currency="USD",
            shipping_address={},
            customer_email="test@example.com",
            created_at=today,
            paid_at=today
        )
        db_session.add(order)
        db_session.flush()

        # Item without template_version
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name="Test Product",
            quantity=1,
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
            customization_data={}  # No template_version
        )
        db_session.add(item)
        db_session.commit()

        report_service = ReportService(db_session)
        result = report_service.generate_sales_report(
            start_date=today.date(),
            end_date=today.date()
        )

        # Should still include the item with null template_version
        assert len(result) == 1
        assert result[0].template_version is None


class TestSalesReportItem:
    """Test suite for SalesReportItem data class."""

    def test_create_sales_report_item_with_all_fields(self):
        """Should create SalesReportItem with all required fields."""
        product_id = uuid4()

        item = SalesReportItem(
            product_id=product_id,
            product_name="Test Product",
            template_version=1,
            total_quantity=10,
            total_revenue=Decimal("199.90"),
            order_count=5
        )

        assert item.product_id == product_id
        assert item.product_name == "Test Product"
        assert item.template_version == 1
        assert item.total_quantity == 10
        assert item.total_revenue == Decimal("199.90")
        assert item.order_count == 5

    def test_sales_report_item_converts_to_dict(self):
        """Should convert SalesReportItem to dictionary for API response."""
        product_id = uuid4()

        item = SalesReportItem(
            product_id=product_id,
            product_name="Test Product",
            template_version=2,
            total_quantity=5,
            total_revenue=Decimal("99.95"),
            order_count=3
        )

        result = item.to_dict()

        assert isinstance(result, dict)
        assert result["product_id"] == str(product_id)
        assert result["product_name"] == "Test Product"
        assert result["template_version"] == 2
        assert result["total_quantity"] == 5
        assert result["total_revenue"] == "99.95"
        assert result["order_count"] == 3

    def test_sales_report_item_handles_null_template_version(self):
        """Should handle null template_version in to_dict."""
        product_id = uuid4()

        item = SalesReportItem(
            product_id=product_id,
            product_name="Test Product",
            template_version=None,
            total_quantity=5,
            total_revenue=Decimal("99.95"),
            order_count=3
        )

        result = item.to_dict()

        assert result["template_version"] is None
