"""
Test AINative API connection.

This script verifies connectivity to the AINative API and validates credentials.
"""
import asyncio
import httpx
import sys

AINATIVE_API_URL = "https://api.ainative.studio/"
AINATIVE_API_TOKEN = "kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM"


async def test_connection():
    """Test AINative API connection."""
    print("=" * 60)
    print("Testing AINative API Connection")
    print("=" * 60)

    url = f"{AINATIVE_API_URL}v1/public/projects"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            print("\n✅ Successfully connected to AINative API")
            projects = response.json()
            print(f"\n📊 Response Status: {response.status_code}")
            print(f"📦 Projects Found: {len(projects) if isinstance(projects, list) else 'N/A'}")
            print(f"\n📋 Full Response:")
            print(response.json())
            return True
        else:
            print(f"\n❌ Connection failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except httpx.TimeoutException:
        print("\n❌ Connection timeout - API may be unreachable")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
