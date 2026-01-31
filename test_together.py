#!/usr/bin/env python
"""
Quick test script for Together AI integration.

Usage:
    export TOGETHER_API_KEY="your-key"
    python test_together.py
"""

import os
import sys


def check_environment():
    """Check if environment is set up correctly."""
    print("🔍 Checking environment...")

    if not os.environ.get("TOGETHER_API_KEY"):
        print("❌ TOGETHER_API_KEY not set")
        print("\nTo fix:")
        print("  1. Get API key from https://together.ai")
        print("  2. Run: export TOGETHER_API_KEY='your-key'")
        return False

    print("✅ TOGETHER_API_KEY found")

    try:
        import maven
        print(f"✅ MAVEN {maven.__version__} installed")
    except ImportError:
        print("❌ MAVEN not installed")
        print("\nTo fix:")
        print("  pip install -e .")
        return False

    return True


def test_basic():
    """Test basic Together AI verification."""
    from maven import ConsensusOrchestrator

    print("\n" + "="*60)
    print("Testing Together AI with MAVEN")
    print("="*60)

    # Use smaller, faster models for quick testing
    models = [
        "together/llama-3.1-8b",
        "together/qwen-2.5-7b",
        "together/mixtral-8x7b",
    ]

    print(f"\nModels: {', '.join(models)}")

    orchestrator = ConsensusOrchestrator(
        models=models,
        config={
            "max_iterations": 2,
            "consensus_threshold": 0.7,
        }
    )

    query = "What is 2 + 2?"
    print(f"\nQuery: {query}")
    print("\n⏳ Running verification...")

    try:
        result = orchestrator.verify(query)

        print("\n" + "="*60)
        print("RESULT")
        print("="*60)
        print(f"\n✅ Consensus: {result.consensus}")
        print(f"📊 Confidence: {result.confidence:.1f}%")
        print(f"🔄 Iterations: {result.iterations}")

        if result.dissent:
            print(f"⚠️  Dissent: {result.dissent}")

        print("\n" + "="*60)
        print("SUCCESS! Together AI integration working.")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_variety():
    """Test with different model sizes."""
    from maven import ConsensusOrchestrator

    print("\n" + "="*60)
    print("Testing with larger models")
    print("="*60)

    models = [
        "together/llama-3.3-70b",
        "together/mixtral-8x22b",
        "together/qwen-2.5-72b",
    ]

    print(f"\nModels: {', '.join(models)}")

    orchestrator = ConsensusOrchestrator(
        models=models,
        config={"max_iterations": 2}
    )

    query = "What is the capital of Japan?"
    print(f"\nQuery: {query}")
    print("\n⏳ Running verification (this may take longer)...")

    try:
        result = orchestrator.verify(query)

        print(f"\n✅ Consensus: {result.consensus}")
        print(f"📊 Confidence: {result.confidence:.1f}%")
        print(f"🔄 Iterations: {result.iterations}")

        return True

    except Exception as e:
        print(f"\n⚠️  Warning: {e}")
        print("(Larger models may require more API credits)")
        return False


def main():
    """Main test runner."""
    print("🚀 MAVEN + Together AI Test Script")
    print()

    if not check_environment():
        sys.exit(1)

    print("\n" + "="*60)
    print("Test 1: Basic verification with small models")
    print("="*60)

    if not test_basic():
        print("\n❌ Basic test failed")
        sys.exit(1)

    print("\n\n" + "="*60)
    print("Test 2: Larger models (optional)")
    print("="*60)

    response = input("\nRun test with larger models? (y/N): ").strip().lower()
    if response == 'y':
        test_model_variety()
    else:
        print("Skipping larger model test")

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
    print("\nNext steps:")
    print("  - Try examples/together_ai_example.py")
    print("  - Check docs/QUICKSTART.md for more options")
    print("  - Run full test suite: pytest tests/ -v")


if __name__ == "__main__":
    main()
