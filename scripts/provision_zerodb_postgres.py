#!/usr/bin/env python3
"""
Provision ZeroDB PostgreSQL instance via AINative API.

This script:
1. Provisions a dedicated PostgreSQL instance on ZeroDB
2. Stores connection details securely
3. Creates the database schema for orders
4. Tests the connection
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv, set_key

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()


class ZeroDBProvisioner:
    """Handle ZeroDB PostgreSQL provisioning."""

    def __init__(self):
        """Initialize the provisioner with API credentials."""
        self.api_url = os.getenv("AINATIVE_API_URL", "https://api.ainative.studio")
        self.api_token = os.getenv("AINATIVE_API_TOKEN")
        self.project_id = os.getenv("ZERODB_PROJECT_ID")

        if not self.api_token:
            raise ValueError("AINATIVE_API_TOKEN not found in environment")
        if not self.project_id or self.project_id == "your-project-id-here":
            raise ValueError("ZERODB_PROJECT_ID not configured in .env file")

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def check_existing_instance(self) -> Optional[Dict[str, Any]]:
        """Check if a PostgreSQL instance already exists."""
        url = f"{self.api_url}/v1/public/projects/{self.project_id}/postgres"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"Warning: Unexpected status code {response.status_code} when checking instance")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error checking existing instance: {e}")
            return None

    def provision_instance(self, plan: str = "starter", region: str = "us-west-2") -> Dict[str, Any]:
        """
        Provision a new PostgreSQL instance.

        Args:
            plan: The pricing plan (e.g., "starter", "professional")
            region: The AWS region (e.g., "us-west-2", "us-east-1")

        Returns:
            Connection details and instance information
        """
        url = f"{self.api_url}/v1/public/projects/{self.project_id}/postgres"

        payload = {
            "plan": plan,
            "region": region
        }

        print(f"\nProvisioning PostgreSQL instance...")
        print(f"  Plan: {plan}")
        print(f"  Region: {region}")
        print(f"  Project ID: {self.project_id}")

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if response.status_code in (200, 201):
                data = response.json()
                print("\n✓ PostgreSQL instance provisioned successfully!")
                return data
            else:
                print(f"\n✗ Error provisioning instance: {response.status_code}")
                print(f"Response: {response.text}")
                raise Exception(f"Failed to provision instance: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"\n✗ Network error: {e}")
            raise

    def get_connection_details(self) -> Optional[Dict[str, Any]]:
        """Get connection details for the PostgreSQL instance."""
        url = f"{self.api_url}/v1/public/projects/{self.project_id}/postgres/connection"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting connection details: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting connection details: {e}")
            return None

    def update_env_file(self, connection_details: Dict[str, Any]) -> None:
        """
        Update .env file with ZeroDB connection details.

        Args:
            connection_details: Connection information from ZeroDB API
        """
        env_file = project_root / ".env"

        # Extract connection details
        host = connection_details.get("host")
        port = connection_details.get("port", 5432)
        database = connection_details.get("database")
        username = connection_details.get("username")
        password = connection_details.get("password")

        if not all([host, database, username, password]):
            raise ValueError("Incomplete connection details received from API")

        # Construct DATABASE_URL
        zerodb_url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

        # Store individual connection details for reference
        print(f"\nUpdating .env file with ZeroDB connection details...")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Database: {database}")
        print(f"  Username: {username}")

        # Update .env file
        set_key(str(env_file), "ZERODB_HOST", host)
        set_key(str(env_file), "ZERODB_PORT", str(port))
        set_key(str(env_file), "ZERODB_DATABASE", database)
        set_key(str(env_file), "ZERODB_USERNAME", username)
        set_key(str(env_file), "ZERODB_PASSWORD", password)
        set_key(str(env_file), "ZERODB_URL", zerodb_url)

        print("\n✓ Environment file updated successfully!")
        print(f"\nConnection details stored in {env_file}")

    def test_connection(self, connection_details: Dict[str, Any]) -> bool:
        """
        Test the database connection.

        Args:
            connection_details: Connection information

        Returns:
            True if connection successful, False otherwise
        """
        try:
            from sqlalchemy import create_engine, text

            host = connection_details.get("host")
            port = connection_details.get("port", 5432)
            database = connection_details.get("database")
            username = connection_details.get("username")
            password = connection_details.get("password")

            url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

            print("\nTesting database connection...")
            engine = create_engine(url, pool_pre_ping=True)

            with engine.connect() as conn:
                # Test basic query
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✓ Connection successful!")
                print(f"  PostgreSQL version: {version[:50]}...")

                # Test schema query
                result = conn.execute(text("SELECT current_database(), current_user"))
                db_name, user = result.fetchone()
                print(f"  Database: {db_name}")
                print(f"  User: {user}")

            engine.dispose()
            return True

        except Exception as e:
            print(f"✗ Connection test failed: {e}")
            return False

    def display_summary(self, connection_details: Dict[str, Any]) -> None:
        """Display a summary of the provisioned instance."""
        print("\n" + "=" * 60)
        print("ZERODB POSTGRESQL INSTANCE PROVISIONED")
        print("=" * 60)
        print(f"\nHost:     {connection_details.get('host')}")
        print(f"Port:     {connection_details.get('port', 5432)}")
        print(f"Database: {connection_details.get('database')}")
        print(f"Username: {connection_details.get('username')}")
        print(f"\nConnection details have been stored in .env file")
        print("\nNext steps:")
        print("  1. Run the schema creation script to set up tables")
        print("  2. Update your application to use ZERODB_URL")
        print("  3. Run migrations or schema sync")
        print("=" * 60 + "\n")


def main():
    """Main provisioning workflow."""
    print("=" * 60)
    print("ZERODB POSTGRESQL PROVISIONER")
    print("=" * 60)

    try:
        provisioner = ZeroDBProvisioner()

        # Check for existing instance
        print("\nChecking for existing PostgreSQL instance...")
        existing = provisioner.check_existing_instance()

        if existing:
            print("✓ PostgreSQL instance already exists!")
            connection_details = existing
        else:
            print("No existing instance found.")

            # Provision new instance
            response = provisioner.provision_instance(
                plan="starter",
                region="us-west-2"
            )

            # Extract connection details from response
            connection_details = response.get("connection_details") or response

        # Update environment file
        provisioner.update_env_file(connection_details)

        # Test connection
        if provisioner.test_connection(connection_details):
            provisioner.display_summary(connection_details)
            print("\n✓ Provisioning completed successfully!")
            return 0
        else:
            print("\n✗ Connection test failed. Please check the connection details.")
            return 1

    except Exception as e:
        print(f"\n✗ Provisioning failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
