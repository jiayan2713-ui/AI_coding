#!/usr/bin/env python
"""Test DeepSeek models endpoint"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

async def test_endpoint(endpoint):
    url = BASE_URL + endpoint
    print(f"\nTesting {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  Response keys: {list(data.keys())}")
                    if 'data' in data:
                        for model in data['data']:
                            print(f"    - {model.get('id')} ({model.get('object')})")
                except:
                    print(f"  Response: {response.text[:500]}")
            else:
                print(f"  Response: {response.text[:500]}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")

async def main():
    endpoints = [
        "/v1/models",
        "/models",
        "/v1/engines",
        "/engines"
    ]

    for endpoint in endpoints:
        await test_endpoint(endpoint)

if __name__ == "__main__":
    asyncio.run(main())