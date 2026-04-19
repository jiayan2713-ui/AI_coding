#!/usr/bin/env python
"""Test with requests library"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_post(endpoint, payload):
    url = BASE_URL + endpoint
    print(f"\nPOST {url}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  JSON keys: {list(data.keys())}")
            except:
                pass
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")

# Test chat endpoint (should work)
print("=" * 60)
print("Testing chat endpoint")
test_post("/v1/chat/completions", {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
})

# Test embeddings endpoint with various model names
print("\n" + "=" * 60)
print("Testing embeddings endpoint")

models = ["deepseek-embedding", "embedding", "text-embedding-3-small", "text-embedding-ada-002"]

for model in models:
    print(f"\nModel: {model}")
    test_post("/v1/embeddings", {
        "model": model,
        "input": ["test text"]
    })

# Test non-versioned endpoint
print("\n" + "=" * 60)
print("Testing non-versioned embeddings endpoint")
test_post("/embeddings", {
    "model": "deepseek-embedding",
    "input": ["test text"]
})

# Test with verify=False
print("\n" + "=" * 60)
print("Testing with verify=False")
import urllib3
urllib3.disable_warnings()
try:
    response = requests.post(
        BASE_URL + "/v1/embeddings",
        headers=headers,
        json={"model": "deepseek-embedding", "input": ["test"]},
        timeout=30,
        verify=False
    )
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")