#!/usr/bin/env python
"""Test the updated DeepSeek client"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.deepseek_client import create_deepseek_client

async def test_embeddings():
    """Test embeddings"""
    print("Creating DeepSeek client...")
    client = create_deepseek_client()
    print(f"Client config: {client.config}")

    print("\nTesting embeddings with single text...")
    try:
        embeddings = await client.get_embeddings(["Hello, world!"])
        print(f"Success! Got {len(embeddings)} embedding(s)")
        if embeddings:
            print(f"First embedding length: {len(embeddings[0].embedding)}")
            print(f"Total tokens: {embeddings[0].total_tokens}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def test_chat():
    """Test chat"""
    print("\nTesting chat completion...")
    client = create_deepseek_client()
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    try:
        response = await client.chat_completion(messages, max_tokens=50)
        print(f"Success! Response: {response.response[:100]}...")
        print(f"Total tokens: {response.total_tokens}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("=" * 60)
    print("Testing DeepSeek Client")
    print("=" * 60)
    await test_embeddings()
    await test_chat()

if __name__ == "__main__":
    asyncio.run(main())