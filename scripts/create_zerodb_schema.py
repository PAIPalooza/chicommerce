#!/usr/bin/env python3
"""
Create database schema for orders on ZeroDB PostgreSQL instance.

This script creates:
- orders table
- order_items table
- payment_events table
- All necessary foreign key constraints
- Performance indexes
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()


class SchemaCreator:
    """Handle database schema creation."""

    def __init__(self):
        """Initialize with ZeroDB connection."""
        self.zerodb_url = os.getenv("ZERODB_URL")

        if not self.zerodb_url:
            raise ValueError(
                "ZERODB_URL not found in environment. "
                "Please run provision_zerodb_postgres.py first."
            )

        print(f"Connecting to ZeroDB...")
        self.engine = create_engine(self.zerodb_url, pool_pre_ping=True)

    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

    def create_orders_table(self) -> None:
        """Create the orders table with all necessary columns and indexes."""
        print("\nCreating orders table...")

        if self.check_table_exists("orders"):
            print("  ⊕ orders table already exists, skipping...")
            return

        sql = text("""
        CREATE TABLE orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cart_id UUID NOT NULL,
            user_id UUID,
            session_id VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'created',

            -- Payment information
            payment_provider VARCHAR(50),
            payment_intent_id VARCHAR(255),
            payment_status VARCHAR(50),

            -- Financial details
            subtotal NUMERIC(10, 2) NOT NULL,
            tax NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            shipping_cost NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            total NUMERIC(10, 2) NOT NULL,
            currency VARCHAR(3) NOT NULL DEFAULT 'USD',

            -- Shipping information
            shipping_address JSONB NOT NULL,
            billing_address JSONB,
            tracking_url VARCHAR(500),

            -- Contact information
            customer_email VARCHAR(255) NOT NULL,
            customer_phone VARCHAR(50),

            -- Order notes and metadata
            notes TEXT,
            order_metadata JSONB NOT NULL DEFAULT '{}',

            -- Timestamps
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            paid_at TIMESTAMP,

            -- Indexes
            CONSTRAINT chk_status CHECK (status IN (
                'created', 'pending_payment', 'paid', 'failed',
                'processing', 'shipped', 'delivered', 'cancelled', 'refunded'
            ))
        );

        -- Create indexes for performance
        CREATE INDEX idx_orders_cart_id ON orders(cart_id);
        CREATE INDEX idx_orders_user_id ON orders(user_id);
        CREATE INDEX idx_orders_session_id ON orders(session_id);
        CREATE INDEX idx_orders_status ON orders(status);
        CREATE INDEX idx_orders_payment_intent_id ON orders(payment_intent_id);
        CREATE INDEX idx_orders_customer_email ON orders(customer_email);
        CREATE INDEX idx_orders_tracking_url ON orders(tracking_url);
        CREATE INDEX idx_order_status_created ON orders(status, created_at);

        -- Create trigger for updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)

        with self.engine.connect() as conn:
            conn.execute(sql)
            conn.commit()

        print("  ✓ orders table created successfully!")

    def create_order_items_table(self) -> None:
        """Create the order_items table with foreign key constraints."""
        print("\nCreating order_items table...")

        if self.check_table_exists("order_items"):
            print("  ⊕ order_items table already exists, skipping...")
            return

        sql = text("""
        CREATE TABLE order_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL,
            product_id UUID NOT NULL,

            -- Item details (snapshot at time of order)
            product_name VARCHAR(255) NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price NUMERIC(10, 2) NOT NULL,
            total_price NUMERIC(10, 2) NOT NULL,

            -- Customization data
            customization_data JSONB NOT NULL DEFAULT '{}',

            -- Timestamps
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),

            -- Foreign key constraints
            CONSTRAINT fk_order_items_order
                FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE,

            -- Constraints
            CONSTRAINT chk_quantity CHECK (quantity > 0),
            CONSTRAINT chk_unit_price CHECK (unit_price >= 0),
            CONSTRAINT chk_total_price CHECK (total_price >= 0)
        );

        -- Create indexes for performance
        CREATE INDEX idx_order_items_order_id ON order_items(order_id);
        CREATE INDEX idx_order_items_product_id ON order_items(product_id);
        """)

        with self.engine.connect() as conn:
            conn.execute(sql)
            conn.commit()

        print("  ✓ order_items table created successfully!")

    def create_payment_events_table(self) -> None:
        """Create the payment_events table for audit trail and idempotency."""
        print("\nCreating payment_events table...")

        if self.check_table_exists("payment_events"):
            print("  ⊕ payment_events table already exists, skipping...")
            return

        sql = text("""
        CREATE TABLE payment_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL,

            -- Event details
            event_id VARCHAR(255) UNIQUE NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            provider VARCHAR(50) NOT NULL,

            -- Payment information
            payment_intent_id VARCHAR(255),
            amount NUMERIC(10, 2),
            currency VARCHAR(3),

            -- Event payload and processing
            payload JSONB NOT NULL,
            processed BOOLEAN NOT NULL DEFAULT FALSE,
            processed_at TIMESTAMP,
            processing_error TEXT,

            -- Timestamps
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),

            -- Foreign key constraints
            CONSTRAINT fk_payment_events_order
                FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE,

            -- Constraints
            CONSTRAINT chk_provider CHECK (provider IN ('stripe', 'paypal'))
        );

        -- Create indexes for performance and idempotency
        CREATE INDEX idx_payment_events_order_id ON payment_events(order_id);
        CREATE INDEX idx_payment_events_event_id ON payment_events(event_id);
        CREATE INDEX idx_payment_event_provider ON payment_events(provider, event_type);
        CREATE INDEX idx_payment_event_processed ON payment_events(processed, created_at);
        """)

        with self.engine.connect() as conn:
            conn.execute(sql)
            conn.commit()

        print("  ✓ payment_events table created successfully!")

    def verify_schema(self) -> None:
        """Verify that all tables and constraints were created correctly."""
        print("\nVerifying schema...")

        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        required_tables = ["orders", "order_items", "payment_events"]
        for table in required_tables:
            if table in tables:
                print(f"  ✓ {table} table exists")

                # Get column count
                columns = inspector.get_columns(table)
                print(f"    - {len(columns)} columns")

                # Get index count
                indexes = inspector.get_indexes(table)
                print(f"    - {len(indexes)} indexes")

                # Get foreign keys
                foreign_keys = inspector.get_foreign_keys(table)
                if foreign_keys:
                    print(f"    - {len(foreign_keys)} foreign key constraints")
            else:
                print(f"  ✗ {table} table missing!")

    def run_sample_queries(self) -> None:
        """Run sample queries to test the schema."""
        print("\nRunning sample queries...")

        queries = [
            ("Count orders", "SELECT COUNT(*) FROM orders"),
            ("Count order items", "SELECT COUNT(*) FROM order_items"),
            ("Count payment events", "SELECT COUNT(*) FROM payment_events"),
            ("List indexes on orders", """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'orders'
                ORDER BY indexname
            """),
        ]

        with self.engine.connect() as conn:
            for description, query in queries:
                try:
                    result = conn.execute(text(query))
                    if "COUNT" in query:
                        count = result.fetchone()[0]
                        print(f"  ✓ {description}: {count}")
                    else:
                        rows = result.fetchall()
                        print(f"  ✓ {description}: {len(rows)} results")
                except Exception as e:
                    print(f"  ✗ {description} failed: {e}")

    def create_all(self) -> None:
        """Create all tables and verify the schema."""
        try:
            # Create tables in order (respecting foreign key dependencies)
            self.create_orders_table()
            self.create_order_items_table()
            self.create_payment_events_table()

            # Verify schema
            self.verify_schema()

            # Run sample queries
            self.run_sample_queries()

            print("\n✓ Schema creation completed successfully!")

        except Exception as e:
            print(f"\n✗ Schema creation failed: {e}")
            import traceback
            traceback.print_exc()
            raise

        finally:
            self.engine.dispose()


def main():
    """Main schema creation workflow."""
    print("=" * 60)
    print("ZERODB SCHEMA CREATOR")
    print("=" * 60)

    try:
        creator = SchemaCreator()
        creator.create_all()
        return 0

    except Exception as e:
        print(f"\n✗ Failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
