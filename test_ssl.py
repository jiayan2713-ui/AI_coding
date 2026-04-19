#!/usr/bin/env python
"""Test SSL connectivity to DeepSeek API"""

import ssl
import sys
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

def test_ssl_version():
    """Check SSL version"""
    print("Python version:", sys.version)
    print("SSL version:", ssl.OPENSSL_VERSION)
    print("SSL version info:", ssl.OPENSSL_VERSION_INFO)

async def test_https_connectivity():
    """Test general HTTPS connectivity"""
    print("\n--- Testing general HTTPS connectivity ---")
    test_urls = [
        "https://www.google.com",
        "https://api.deepseek.com",
        "https://httpbin.org/status/200"
    ]

    for url in test_urls:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                print(f"{url}: Status {response.status_code}")
        except Exception as e:
            print(f"{url}: Error {type(e).__name__}: {e}")

async def test_deepseek_api():
    """Test DeepSeek API connectivity"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not found in environment")
        return

    print(f"\n--- Testing DeepSeek API ---")
    print(f"Testing API key: {api_key[:10]}...")
    print(f"Base URL: {base_url}")

    # Test different endpoint paths
    endpoint_candidates = [
        "/embeddings",
        "/v1/embeddings",
        "/chat/completions",
        "/v1/chat/completions"
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for endpoint in endpoint_candidates:
        url = base_url + endpoint
        print(f"\nTrying endpoint: {endpoint}")

        # Simple payload based on endpoint
        if "embedding" in endpoint:
            payload = {"model": "deepseek-embedding", "input": ["test"]}
        else:
            payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}

        try:
            # Try with default SSL settings
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                print(f"  Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"  Response: {response.text[:200]}")
                else:
                    print(f"  Success!")
                    # Try to parse response
                    try:
                        data = response.json()
                        print(f"  Response keys: {list(data.keys())}")
                    except:
                        print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"  Error: {type(e).__name__}: {e}")

        # Try with SSL verify=False
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(url, headers=headers, json=payload)
                print(f"  With verify=False: Status {response.status_code}")
        except Exception as e:
            print(f"  With verify=False: Error {type(e).__name__}: {e}")

    # Test with custom SSL context
    print("\n--- Testing with custom SSL context ---")
    ssl_context = ssl.create_default_context()
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    url = base_url + "/embeddings"
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=ssl_context) as client:
            response = await client.post(url, headers=headers, json={"model": "deepseek-embedding", "input": ["test"]})
            print(f"Custom SSL context: Status {response.status_code}")
    except Exception as e:
        print(f"Custom SSL context: Error {type(e).__name__}: {e}")

def test_curl():
    """Test with curl command"""
    import subprocess
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return

    # Try to run curl if available
    try:
        print("\n--- Testing with curl ---")
        cmd = [
            "curl", "-X", "POST", "https://api.deepseek.com/embeddings",
            "-H", "Authorization: Bearer " + api_key,
            "-H", "Content-Type: application/json",
            "-d", '{"model":"deepseek-embedding","input":["test"]}',
            "-v"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"curl exit code: {result.returncode}")
        print(f"curl stdout: {result.stdout[:500]}")
        print(f"curl stderr: {result.stderr[:500]}")
    except Exception as e:
        print(f"curl test failed: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("SSL Connectivity Test for DeepSeek API")
    print("=" * 60)

    test_ssl_version()

    # Run async tests
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_https_connectivity())
    loop.run_until_complete(test_deepseek_api())

    test_curl()

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)