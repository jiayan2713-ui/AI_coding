#!/usr/bin/env python
"""Test SSL handshake with DeepSeek API"""

import socket
import ssl
import sys

def test_ssl_handshake(hostname="api.deepseek.com", port=443):
    """Test SSL handshake with different TLS versions"""
    print(f"Testing SSL handshake to {hostname}:{port}")

    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    # Wrap with SSL context
    context = ssl.create_default_context()

    # Test different TLS versions
    tls_versions = [
        (ssl.PROTOCOL_TLSv1_2, "TLSv1.2"),
        (ssl.PROTOCOL_TLSv1_1, "TLSv1.1"),
        (ssl.PROTOCOL_TLS, "TLS (default)"),
    ]

    for protocol, name in tls_versions:
        try:
            print(f"\nTrying {name}...")
            # Create new context for each protocol
            context = ssl.SSLContext(protocol)
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            # Wrap socket
            ssl_sock = context.wrap_socket(sock, server_hostname=hostname)

            # Connect
            ssl_sock.connect((hostname, port))

            # Get certificate
            cert = ssl_sock.getpeercert()
            print(f"  Success! Connected using {ssl_sock.version()}")
            print(f"  Cipher: {ssl_sock.cipher()}")
            print(f"  Certificate issuer: {cert.get('issuer', 'N/A')}")

            ssl_sock.close()
            return True
        except Exception as e:
            print(f"  Failed: {type(e).__name__}: {e}")

    sock.close()
    return False

def test_endpoint_ssl(endpoint_path="/embeddings"):
    """Test SSL handshake to specific endpoint (full URL)"""
    import httpx
    from dotenv import load_dotenv
    import os

    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = "https://api.deepseek.com"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = base_url + endpoint_path
    print(f"\n\nTesting endpoint: {url}")

    # Try different SSL configurations
    configs = [
        {"verify": True, "http2": False, "name": "Default"},
        {"verify": False, "http2": False, "name": "No verify"},
        {"verify": True, "http2": True, "name": "HTTP/2"},
        {"verify": ssl.create_default_context(), "http2": False, "name": "Custom SSL context"},
    ]

    for config in configs:
        print(f"\n  Config: {config['name']}")
        try:
            client = httpx.AsyncClient(
                timeout=30.0,
                verify=config['verify'],
                http2=config['http2']
            )
            # We'll just test connection with a simple request
            import asyncio
            async def test():
                response = await client.post(url, headers=headers, json={"model": "deepseek-embedding", "input": ["test"]})
                return response
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(test())
            print(f"    Status: {response.status_code}")
            print(f"    Response length: {len(response.text)}")
            client.close()
        except Exception as e:
            print(f"    Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("SSL Handshake Test")
    print("=" * 60)

    # Test basic SSL handshake
    test_ssl_handshake()

    # Test specific endpoints
    test_endpoint_ssl("/v1/embeddings")
    test_endpoint_ssl("/embeddings")

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)