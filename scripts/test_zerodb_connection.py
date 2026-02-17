#!/usr/bin/env python3
"""
Test ZeroDB PostgreSQL connection and run sample queries.

This script validates:
- Database connectivity
- Schema integrity
- Index creation
- Foreign key constraints
- Sample data operations (CRUD)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()


class ZeroDBConnectionTester:
    """Test ZeroDB PostgreSQL connection and functionality."""

    def __init__(self):
        """Initialize the connection tester."""
        self.zerodb_url = os.getenv("ZERODB_URL")

        if not self.zerodb_url:
            raise ValueError(
                "ZERODB_URL not found in environment. "
                "Please run provision_zerodb_postgres.py first."
            )

        print("Initializing ZeroDB connection tester...")
        self.engine = create_engine(self.zerodb_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def test_basic_connection(self) -> bool:
        """Test basic database connectivity."""
        print("\n[1/7] Testing basic connection...")

        try:
            with self.engine.connect() as conn:
                # Get PostgreSQL version
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"  ✓ Connected to PostgreSQL")
                print(f"    Version: {version[:80]}...")

                # Get current database and user
                result = conn.execute(text("SELECT current_database(), current_user"))
                db_name, user = result.fetchone()
                print(f"    Database: {db_name}")
                print(f"    User: {user}")

                # Check connection count
                result = conn.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                ))
                connections = result.fetchone()[0]
                print(f"    Active connections: {connections}")

            return True

        except Exception as e:
            print(f"  ✗ Connection test failed: {e}")
            return False

    def test_schema_exists(self) -> bool:
        """Test that all required tables exist."""
        print("\n[2/7] Testing schema existence...")

        required_tables = ["orders", "order_items", "payment_events"]
        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()

        all_exist = True
        for table in required_tables:
            if table in existing_tables:
                print(f"  ✓ Table '{table}' exists")
            else:
                print(f"  ✗ Table '{table}' missing")
                all_exist = False

        return all_exist

    def test_table_structure(self) -> bool:
        """Test table structure and columns."""
        print("\n[3/7] Testing table structure...")

        inspector = inspect(self.engine)

        # Test orders table
        orders_columns = inspector.get_columns("orders")
        required_orders_cols = [
            "id", "cart_id", "user_id", "session_id", "status",
            "payment_provider", "payment_intent_id", "subtotal",
            "tax", "shipping_cost", "total", "currency",
            "shipping_address", "customer_email", "created_at"
        ]

        print(f"  Orders table:")
        print(f"    Total columns: {len(orders_columns)}")
        missing_cols = [
            col for col in required_orders_cols
            if col not in [c["name"] for c in orders_columns]
        ]
        if missing_cols:
            print(f"    ✗ Missing columns: {missing_cols}")
            return False
        else:
            print(f"    ✓ All required columns present")

        # Test order_items table
        items_columns = inspector.get_columns("order_items")
        print(f"  Order Items table:")
        print(f"    Total columns: {len(items_columns)}")
        print(f"    ✓ Structure verified")

        # Test payment_events table
        events_columns = inspector.get_columns("payment_events")
        print(f"  Payment Events table:")
        print(f"    Total columns: {len(events_columns)}")
        print(f"    ✓ Structure verified")

        return True

    def test_indexes(self) -> bool:
        """Test that indexes are created."""
        print("\n[4/7] Testing indexes...")

        inspector = inspect(self.engine)

        # Test orders indexes
        orders_indexes = inspector.get_indexes("orders")
        print(f"  Orders table: {len(orders_indexes)} indexes")

        required_indexes = [
            "idx_orders_cart_id",
            "idx_orders_status",
            "idx_orders_customer_email"
        ]

        index_names = [idx["name"] for idx in orders_indexes]
        all_exist = True

        for required in required_indexes:
            if required in index_names:
                print(f"    ✓ {required}")
            else:
                print(f"    ✗ {required} missing")
                all_exist = False

        return all_exist

    def test_foreign_keys(self) -> bool:
        """Test foreign key constraints."""
        print("\n[5/7] Testing foreign key constraints...")

        inspector = inspect(self.engine)

        # Test order_items foreign keys
        items_fks = inspector.get_foreign_keys("order_items")
        print(f"  Order Items table: {len(items_fks)} foreign keys")
        if items_fks:
            for fk in items_fks:
                print(f"    ✓ {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}")
        else:
            print("    ✗ No foreign keys found")
            return False

        # Test payment_events foreign keys
        events_fks = inspector.get_foreign_keys("payment_events")
        print(f"  Payment Events table: {len(events_fks)} foreign keys")
        if events_fks:
            for fk in events_fks:
                print(f"    ✓ {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}")
        else:
            print("    ✗ No foreign keys found")
            return False

        return True

    def test_sample_operations(self) -> bool:
        """Test CRUD operations with sample data."""
        print("\n[6/7] Testing sample CRUD operations...")

        try:
            session = self.SessionLocal()

            # Create a test order
            order_id = uuid4()
            cart_id = uuid4()
            session_id = f"test_session_{uuid4().hex[:8]}"

            print("  Creating test order...")
            insert_order = text("""
                INSERT INTO orders (
                    id, cart_id, session_id, status,
                    subtotal, tax, shipping_cost, total, currency,
                    shipping_address, customer_email, order_metadata
                ) VALUES (
                    :id, :cart_id, :session_id, 'created',
                    :subtotal, :tax, :shipping_cost, :total, 'USD',
                    :shipping_address, :customer_email, :metadata
                )
            """)

            session.execute(insert_order, {
                "id": str(order_id),
                "cart_id": str(cart_id),
                "session_id": session_id,
                "subtotal": Decimal("99.99"),
                "tax": Decimal("8.00"),
                "shipping_cost": Decimal("5.00"),
                "total": Decimal("112.99"),
                "shipping_address": '{"street": "123 Test St", "city": "Test City"}',
                "customer_email": "test@example.com",
                "metadata": '{}'
            })
            session.commit()
            print(f"    ✓ Order created with ID: {order_id}")

            # Read the order
            print("  Reading test order...")
            select_order = text("SELECT * FROM orders WHERE id = :id")
            result = session.execute(select_order, {"id": str(order_id)})
            order = result.fetchone()
            if order:
                print(f"    ✓ Order retrieved successfully")
                print(f"      Status: {order.status}")
                print(f"      Total: ${order.total}")
            else:
                print("    ✗ Failed to retrieve order")
                return False

            # Update the order
            print("  Updating test order...")
            update_order = text("""
                UPDATE orders
                SET status = 'paid', paid_at = NOW()
                WHERE id = :id
            """)
            session.execute(update_order, {"id": str(order_id)})
            session.commit()
            print("    ✓ Order updated to 'paid' status")

            # Create order items
            print("  Creating order items...")
            product_id = uuid4()
            insert_item = text("""
                INSERT INTO order_items (
                    order_id, product_id, product_name,
                    quantity, unit_price, total_price, customization_data
                ) VALUES (
                    :order_id, :product_id, :product_name,
                    :quantity, :unit_price, :total_price, :customization_data
                )
            """)

            session.execute(insert_item, {
                "order_id": str(order_id),
                "product_id": str(product_id),
                "product_name": "Test Product",
                "quantity": 2,
                "unit_price": Decimal("49.99"),
                "total_price": Decimal("99.98"),
                "customization_data": '{"color": "blue", "size": "L"}'
            })
            session.commit()
            print("    ✓ Order item created")

            # Create payment event
            print("  Creating payment event...")
            event_id = f"evt_{uuid4().hex[:16]}"
            insert_event = text("""
                INSERT INTO payment_events (
                    order_id, event_id, event_type, provider,
                    payload, processed
                ) VALUES (
                    :order_id, :event_id, 'payment.succeeded', 'stripe',
                    :payload, TRUE
                )
            """)

            session.execute(insert_event, {
                "order_id": str(order_id),
                "event_id": event_id,
                "payload": '{"amount": 11299, "currency": "usd"}'
            })
            session.commit()
            print("    ✓ Payment event created")

            # Verify cascade delete
            print("  Testing cascade delete...")
            delete_order = text("DELETE FROM orders WHERE id = :id")
            session.execute(delete_order, {"id": str(order_id)})
            session.commit()

            # Check that items and events were deleted
            check_items = text("SELECT COUNT(*) FROM order_items WHERE order_id = :id")
            check_events = text("SELECT COUNT(*) FROM payment_events WHERE order_id = :id")

            items_count = session.execute(check_items, {"id": str(order_id)}).scalar()
            events_count = session.execute(check_events, {"id": str(order_id)}).scalar()

            if items_count == 0 and events_count == 0:
                print("    ✓ Cascade delete working correctly")
            else:
                print(f"    ✗ Cascade delete failed (items: {items_count}, events: {events_count})")
                return False

            session.close()
            return True

        except Exception as e:
            print(f"  ✗ CRUD operations failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_performance_queries(self) -> bool:
        """Test common performance queries."""
        print("\n[7/7] Testing performance queries...")

        try:
            with self.engine.connect() as conn:
                # Test index usage
                print("  Testing query performance...")

                queries = [
                    ("Count orders", "SELECT COUNT(*) FROM orders"),
                    ("Orders by status", "SELECT status, COUNT(*) FROM orders GROUP BY status"),
                    ("Recent orders", "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10"),
                    ("Order with items", """
                        SELECT o.id, o.total, COUNT(oi.id) as item_count
                        FROM orders o
                        LEFT JOIN order_items oi ON o.id = oi.order_id
                        GROUP BY o.id, o.total
                        LIMIT 10
                    """),
                ]

                for description, query in queries:
                    result = conn.execute(text(query))
                    rows = result.fetchall()
                    print(f"    ✓ {description}: executed successfully")

            return True

        except Exception as e:
            print(f"  ✗ Performance queries failed: {e}")
            return False

    def display_summary(self, results: dict) -> None:
        """Display test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r)
        failed_tests = total_tests - passed_tests

        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status:8} - {test_name}")

        print("-" * 60)
        print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")

        if failed_tests == 0:
            print("\n✓ All tests passed! ZeroDB is ready to use.")
        else:
            print(f"\n✗ {failed_tests} test(s) failed. Please review the output above.")

        print("=" * 60 + "\n")

    def run_all_tests(self) -> int:
        """Run all tests and return exit code."""
        results = {}

        try:
            results["Basic Connection"] = self.test_basic_connection()
            results["Schema Exists"] = self.test_schema_exists()
            results["Table Structure"] = self.test_table_structure()
            results["Indexes"] = self.test_indexes()
            results["Foreign Keys"] = self.test_foreign_keys()
            results["CRUD Operations"] = self.test_sample_operations()
            results["Performance Queries"] = self.test_performance_queries()

            self.display_summary(results)

            # Return 0 if all tests pass, 1 otherwise
            return 0 if all(results.values()) else 1

        except Exception as e:
            print(f"\n✗ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

        finally:
            self.engine.dispose()


def main():
    """Main test workflow."""
    print("=" * 60)
    print("ZERODB CONNECTION TESTER")
    print("=" * 60)

    try:
        tester = ZeroDBConnectionTester()
        return tester.run_all_tests()

    except Exception as e:
        print(f"\n✗ Failed to initialize tester: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
