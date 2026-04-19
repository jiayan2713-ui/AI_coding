#!/usr/bin/env python
"""Test DeepSeek embeddings endpoint variations"""

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

async def test_endpoint(endpoint, model_name):
    """Test a specific endpoint with model name"""
    url = BASE_URL + endpoint
    payload = {
        "model": model_name,
        "input": ["test text for embedding"]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            return {
                "endpoint": endpoint,
                "model": model_name,
                "status": response.status_code,
                "response": response.text[:500] if response.text else ""
            }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "model": model_name,
            "error": str(e),
            "status": None
        }

async def main():
    if not API_KEY:
        print("API key not found")
        return

    print("Testing DeepSeek embeddings endpoints...")

    endpoints = [
        "/v1/embeddings",
        "/v1/embedding",
        "/embeddings",
        "/embedding",
        "/v1/engines/embeddings",
        "/v1/engines/embedding"
    ]

    models = [
        "deepseek-embedding",
        "embedding",
        "text-embedding-3-small",
        "text-embedding-ada-002",
        "deepseek-embedding-v1",
        "embedding-001"
    ]

    # Test each endpoint with each model
    for endpoint in endpoints:
        for model in models:
            print(f"\nTesting {endpoint} with model '{model}'...")
            result = await test_endpoint(endpoint, model)

            if "error" in result:
                print(f"  Error: {result['error']}")
            else:
                print(f"  Status: {result['status']}")
                if result['status'] == 200:
                    print(f"  Success!")
                    # Try to parse response
                    try:
                        import json
                        data = json.loads(result['response'])
                        print(f"  Response keys: {list(data.keys())}")
                        if 'data' in data:
                            print(f"  Embedding length: {len(data['data'][0]['embedding'])}")
                    except:
                        print(f"  Response: {result['response'][:200]}")
                else:
                    print(f"  Response: {result['response'][:200]}")

            # If success, break out of inner loop
            if result.get('status') == 200:
                print(f"\n✅ Found working combination: {endpoint} with model {model}")
                return

if __name__ == "__main__":
    asyncio.run(main())