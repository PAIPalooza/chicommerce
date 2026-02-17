"""
Integration tests for sales reports API endpoint.

Following TDD/BDD approach with descriptive test names for clear test organization.
Tests written BEFORE implementation to ensure proper test-driven development.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4


class TestSalesReportsEndpoint:
    """Test suite for GET /reports/sales endpoint."""

    def test_get_sales_report_requires_authentication(self, client, db_session):
        """Should return 401 when no API key provided."""
        # Remove authentication
        client.set_auth(None)

        response = client.get("/api/v1/reports/sales")

        assert response.status_code == 401
        assert "API key is required" in response.json()["detail"]

    def test_get_sales_report_rejects_invalid_api_key(self, client, db_session):
        """Should return 403 when invalid API key provided."""
        # Set invalid API key
        client.set_auth("invalid-key")

        response = client.get(
            "/api/v1/reports/sales",
            headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 403
        assert "Invalid API Key" in response.json()["detail"]

    def test_get_sales_report_with_valid_authentication(self, client, db_session):
        """Should return 200 with valid admin API key."""
        from app.models import Product, Order, OrderItem

        # Create test data
        product = Product(
            name="Test Product",
            base_price=Decimal("10.00"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        today = datetime.utcnow()

        order = Order(
            cart_id=uuid4(),
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

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name="Test Product",
            quantity=1,
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
            customization_data={"template_version": 1}
        )
        db_session.add(item)
        db_session.commit()

        response = client.get("/api/v1/reports/sales")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_sales_report_with_date_range_filters(self, client, db_session):
        """Should filter results by start and end date query parameters."""
        from app.models import Product, Order, OrderItem

        product = Product(
            name="Test Product",
            base_price=Decimal("10.00"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        # Create orders at different dates
        old_date = datetime.utcnow() - timedelta(days=30)
        recent_date = datetime.utcnow() - timedelta(days=1)

        old_order = Order(
            cart_id=uuid4(),
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
            cart_id=uuid4(),
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

        # Query only recent week
        start_date = (datetime.utcnow() - timedelta(days=7)).date()
        end_date = datetime.utcnow().date()

        response = client.get(
            f"/api/v1/reports/sales?start={start_date}&end={end_date}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["order_count"] == 1

    def test_get_sales_report_returns_grouped_results(self, client, db_session):
        """Should return sales grouped by product_id and template_version."""
        from app.models import Product, Order, OrderItem

        product = Product(
            name="T-Shirt",
            base_price=Decimal("19.99"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        today = datetime.utcnow()

        # Create orders with different template versions
        order1 = Order(
            cart_id=uuid4(),
            session_id="session1",
            status="paid",
            subtotal=Decimal("39.98"),
            tax=Decimal("4.00"),
            shipping_cost=Decimal("8.99"),
            total=Decimal("52.97"),
            currency="USD",
            shipping_address={},
            customer_email="test1@example.com",
            created_at=today,
            paid_at=today
        )
        order2 = Order(
            cart_id=uuid4(),
            session_id="session2",
            status="paid",
            subtotal=Decimal("19.99"),
            tax=Decimal("2.00"),
            shipping_cost=Decimal("8.99"),
            total=Decimal("30.98"),
            currency="USD",
            shipping_address={},
            customer_email="test2@example.com",
            created_at=today,
            paid_at=today
        )
        db_session.add_all([order1, order2])
        db_session.flush()

        item1 = OrderItem(
            order_id=order1.id,
            product_id=product.id,
            product_name="T-Shirt",
            quantity=2,
            unit_price=Decimal("19.99"),
            total_price=Decimal("39.98"),
            customization_data={"template_version": 1}
        )
        item2 = OrderItem(
            order_id=order2.id,
            product_id=product.id,
            product_name="T-Shirt",
            quantity=1,
            unit_price=Decimal("19.99"),
            total_price=Decimal("19.99"),
            customization_data={"template_version": 2}
        )
        db_session.add_all([item1, item2])
        db_session.commit()

        response = client.get("/api/v1/reports/sales")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify structure
        for item in data:
            assert "product_id" in item
            assert "product_name" in item
            assert "template_version" in item
            assert "total_quantity" in item
            assert "total_revenue" in item
            assert "order_count" in item

    def test_get_sales_report_supports_pagination(self, client, db_session):
        """Should support skip and limit query parameters for pagination."""
        from app.models import Product, Order, OrderItem

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

        today = datetime.utcnow()

        # Create order for each product
        for product in products:
            order = Order(
                cart_id=uuid4(),
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

        # Test pagination
        response1 = client.get("/api/v1/reports/sales?skip=0&limit=5")
        response2 = client.get("/api/v1/reports/sales?skip=5&limit=5")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert len(data1) == 5
        assert len(data2) == 5

        # Ensure different results
        ids1 = {(item["product_id"], item["template_version"]) for item in data1}
        ids2 = {(item["product_id"], item["template_version"]) for item in data2}
        assert ids1.isdisjoint(ids2)

    def test_get_sales_report_defaults_to_last_30_days(self, client, db_session):
        """Should default to last 30 days when no date range provided."""
        from app.models import Product, Order, OrderItem

        product = Product(
            name="Test Product",
            base_price=Decimal("10.00"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        # Create order within last 30 days
        recent_date = datetime.utcnow() - timedelta(days=15)

        order = Order(
            cart_id=uuid4(),
            session_id="session",
            status="paid",
            subtotal=Decimal("10.00"),
            tax=Decimal("1.00"),
            shipping_cost=Decimal("5.00"),
            total=Decimal("16.00"),
            currency="USD",
            shipping_address={},
            customer_email="test@example.com",
            created_at=recent_date,
            paid_at=recent_date
        )
        db_session.add(order)
        db_session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name="Test Product",
            quantity=1,
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
            customization_data={"template_version": 1}
        )
        db_session.add(item)
        db_session.commit()

        response = client.get("/api/v1/reports/sales")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_sales_report_returns_empty_list_when_no_data(self, client, db_session):
        """Should return empty list when no orders match criteria."""
        # Query future dates
        start_date = (datetime.utcnow() + timedelta(days=1)).date()
        end_date = (datetime.utcnow() + timedelta(days=7)).date()

        response = client.get(
            f"/api/v1/reports/sales?start={start_date}&end={end_date}"
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_sales_report_validates_date_format(self, client, db_session):
        """Should return 422 when date format is invalid."""
        response = client.get(
            "/api/v1/reports/sales?start=invalid-date&end=2024-12-31"
        )

        assert response.status_code == 422

    def test_get_sales_report_validates_date_range(self, client, db_session):
        """Should return 400 when start date is after end date."""
        start_date = datetime.utcnow().date()
        end_date = (datetime.utcnow() - timedelta(days=7)).date()

        response = client.get(
            f"/api/v1/reports/sales?start={start_date}&end={end_date}"
        )

        assert response.status_code == 400
        assert "start date must be before or equal to end date" in response.json()["detail"].lower()

    def test_get_sales_report_response_format(self, client, db_session):
        """Should return correctly formatted JSON response."""
        from app.models import Product, Order, OrderItem

        product = Product(
            name="Test Product",
            base_price=Decimal("19.99"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()

        today = datetime.utcnow()

        order = Order(
            cart_id=uuid4(),
            session_id="session",
            status="paid",
            subtotal=Decimal("39.98"),
            tax=Decimal("4.00"),
            shipping_cost=Decimal("8.99"),
            total=Decimal("52.97"),
            currency="USD",
            shipping_address={},
            customer_email="test@example.com",
            created_at=today,
            paid_at=today
        )
        db_session.add(order)
        db_session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name="Test Product",
            quantity=2,
            unit_price=Decimal("19.99"),
            total_price=Decimal("39.98"),
            customization_data={"template_version": 1}
        )
        db_session.add(item)
        db_session.commit()

        response = client.get("/api/v1/reports/sales")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        item = data[0]
        assert isinstance(item["product_id"], str)
        assert item["product_name"] == "Test Product"
        assert item["template_version"] == 1
        assert item["total_quantity"] == 2
        assert item["total_revenue"] == "39.98"
        assert item["order_count"] == 1
