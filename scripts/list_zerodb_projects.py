"""
List all existing ZeroDB projects.

This script lists all projects to help identify available projects.
"""
import asyncio
import httpx
import sys
import json

AINATIVE_API_URL = "https://api.ainative.studio/"
AINATIVE_API_TOKEN = "kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM"


async def list_projects():
    """List all existing ZeroDB projects."""
    print("=" * 60)
    print("Listing ZeroDB Projects")
    print("=" * 60)

    url = f"{AINATIVE_API_URL}v1/public/projects"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            projects = response.json()
            print(f"\n✅ Found {len(projects)} projects\n")

            # Filter to show only relevant projects (not test/default projects)
            relevant = [p for p in projects if not p['name'].startswith('Default') and
                       not p['name'].startswith('Test') and
                       not p['name'].startswith('ZeroSchedule')]

            if relevant:
                print("📦 Relevant Projects:")
                print("-" * 60)
                for proj in relevant[:10]:  # Show first 10
                    print(f"\nName: {proj['name']}")
                    print(f"ID: {proj['id']}")
                    print(f"Description: {proj.get('description', 'N/A')}")
                    print(f"Status: {proj['status']}")
                    print(f"Tier: {proj['tier']}")
                    print(f"Tables: {proj.get('usage', {}).get('tables', 0)}")
                    print(f"Created: {proj.get('created_at', 'N/A')[:10]}")

            # Check if ChiCommerce project already exists
            chicommerce = [p for p in projects if 'chicommerce' in p['name'].lower()]
            if chicommerce:
                print("\n" + "=" * 60)
                print("🎯 ChiCommerce Project Found!")
                print("=" * 60)
                for proj in chicommerce:
                    print(f"\nProject ID: {proj['id']}")
                    print(f"Name: {proj['name']}")
                    print(f"Status: {proj['status']}")
                    print("\n⚠️  Add this to your .env file:")
                    print(f"ZERODB_PROJECT_ID={proj['id']}")
                    return proj['id']

            print("\n" + "=" * 60)
            print("💡 No ChiCommerce project found")
            print("=" * 60)
            print("\nOptions:")
            print("1. Use an existing project by copying its ID to .env")
            print("2. Delete unused test/default projects to free up slots")
            print("3. Upgrade to a higher tier")
            return None

        else:
            print(f"\n❌ Failed to list projects: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    project_id = asyncio.run(list_projects())
    sys.exit(0 if project_id is not None else 1)
