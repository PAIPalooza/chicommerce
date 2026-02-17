"""Debug script to check the actual API response."""
import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

AINATIVE_API_URL = os.getenv("AINATIVE_API_URL", "https://api.ainative.studio/")
AINATIVE_API_TOKEN = os.getenv("AINATIVE_API_TOKEN")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")

async def debug_list():
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

asyncio.run(debug_list())
