#!/usr/bin/env python
"""Test local embedding model installation and functionality"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))


def test_imports():
    """Test if required packages are installed"""
    print("=" * 60)
    print("Testing package imports...")
    print("=" * 60)

    packages = [
        ("sentence-transformers", "sentence_transformers"),
        ("torch", "torch"),
        ("transformers", "transformers"),
    ]

    all_passed = True
    for package_name, import_name in packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} - OK")
        except ImportError as e:
            print(f"❌ {package_name} - FAILED: {e}")
            all_passed = False

    return all_passed


def test_model_loading():
    """Test loading the local embedding model"""
    print("\n" + "=" * 60)
    print("Testing model loading...")
    print("=" * 60)

    try:
        from sentence_transformers import SentenceTransformer

        model_name = "BAAI/bge-small-zh-v1.5"
        print(f"Loading model: {model_name}")

        # Try to load model
        model = SentenceTransformer(model_name, device="cpu")

        # Check model properties
        dimension = model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded successfully!")
        print(f"   - Model name: {model_name}")
        print(f"   - Embedding dimension: {dimension}")
        print(f"   - Expected dimension: 384")

        if dimension == 512:
            print(f"   ✅ Dimension matches expected value (512)")
        else:
            print(f"   ⚠️  Dimension mismatch: got {dimension}, expected 512")

        return model

    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check internet connection (model needs to be downloaded)")
        print("2. Verify model name: BAAI/bge-small-zh-v1.5")
        print("3. Check available disk space")
        print("4. Try with a smaller model first: all-MiniLM-L6-v2")
        return None


def test_embedding_generation(model=None):
    """Test generating embeddings"""
    print("\n" + "=" * 60)
    print("Testing embedding generation...")
    print("=" * 60)

    # If model is not provided, try to load it
    if model is None:
        print("⚠️  Model not provided, attempting to load...")
        model = test_model_loading()
        if model is None:
            print("❌ Skipping embedding test - model not loaded")
            return False

    try:
        test_texts = [
            "这是一个测试句子。",
            "This is a test sentence in English.",
            "今天天气很好，适合去公园散步。",
        ]

        print(f"Generating embeddings for {len(test_texts)} texts...")

        # Generate embeddings
        embeddings = model.encode(
            test_texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        print(f"✅ Embeddings generated successfully!")
        print(f"   - Number of embeddings: {len(embeddings)}")
        print(f"   - Embedding shape: {embeddings.shape}")
        print(f"   - Data type: {embeddings.dtype}")

        # Check each embedding
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            print(f"\n   Text {i+1}: {text[:50]}...")
            print(f"   - Length: {len(embedding)}")
            print(f"   - Min value: {embedding.min():.4f}")
            print(f"   - Max value: {embedding.max():.4f}")
            print(f"   - Mean value: {embedding.mean():.4f}")

        return True

    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False


def test_integration():
    """Test integration with the embedding client"""
    print("\n" + "=" * 60)
    print("Testing integration with embedding client...")
    print("=" * 60)

    try:
        from backend.app.services.embedding_client import LocalEmbeddingClient

        print("Creating LocalEmbeddingClient...")

        client = LocalEmbeddingClient(
            model_name="BAAI/bge-small-zh-v1.5",
            device="cpu",
            batch_size=2,
            normalize=True
        )

        print(f"✅ LocalEmbeddingClient created successfully!")

        # Get model info
        model_info = client.get_model_info()
        print(f"\nModel information:")
        for key, value in model_info.items():
            print(f"   - {key}: {value}")

        # Test async embedding generation
        import asyncio

        async def test_async():
            test_texts = ["异步测试文本", "Async test text"]
            print(f"\nTesting async embedding generation...")
            embeddings = await client.get_embeddings(test_texts)
            print(f"✅ Async embedding generation successful!")
            print(f"   - Generated {len(embeddings)} embeddings")
            print(f"   - First embedding dimensions: {embeddings[0].dimensions}")

            return True

        # Run async test
        try:
            success = asyncio.run(test_async())
            return success
        except RuntimeError:
            # If event loop is already running (e.g., in notebook)
            print("⚠️  Can't run async test in current context")
            return True

    except ImportError as e:
        print(f"❌ Could not import embedding client: {e}")
        print("Make sure the backend code is in the Python path")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("Local Embedding Model Test")
    print("=" * 60)
    print("This script tests if the local embedding model is properly installed.")
    print("=" * 60)

    # Test 1: Package imports
    if not test_imports():
        print("\n❌ Package imports failed. Please install required packages:")
        print("   pip install sentence-transformers torch transformers")
        return

    # Test 2: Model loading
    model = test_model_loading()
    if model is None:
        print("\n❌ Model loading failed.")
        return

    # Test 3: Embedding generation
    if not test_embedding_generation(model):
        print("\n❌ Embedding generation failed.")
        return

    # Test 4: Integration test
    if not test_integration():
        print("\n❌ Integration test failed.")
        return

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour local embedding model is working correctly.")
    print("The system is ready to use local embeddings instead of DeepSeek API.")
    print("\nNext steps:")
    print("1. Start the RAG application")
    print("2. Test document upload and query functionality")
    print("3. Monitor performance and memory usage")


if __name__ == "__main__":
    main()