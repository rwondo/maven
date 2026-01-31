"""
Together AI example: Run MAVEN with open-source models.

This example demonstrates using Together AI's hosted models
(Llama, Mistral, Qwen, etc.) for multi-model verification.

Usage:
    export TOGETHER_API_KEY="your-api-key"
    python together_ai_example.py

Requirements:
    - TOGETHER_API_KEY environment variable
    - openai package (pip install openai)

Available model aliases:
    - llama-3.3-70b -> meta-llama/Llama-3.3-70B-Instruct-Turbo
    - llama-3.1-405b -> meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo
    - mixtral-8x22b -> mistralai/Mixtral-8x22B-Instruct-v0.1
    - qwen-2.5-72b -> Qwen/Qwen2.5-72B-Instruct-Turbo
    - deepseek-r1-70b -> deepseek-ai/DeepSeek-R1-Distill-Llama-70B

You can also use full model paths directly:
    - meta-llama/Llama-3.3-70B-Instruct-Turbo
    - mistralai/Mixtral-8x7B-Instruct-v0.1
"""

import os
from maven import ConsensusOrchestrator


def check_api_key():
    """Check if Together AI API key is set."""
    if not os.environ.get("TOGETHER_API_KEY"):
        print("Error: TOGETHER_API_KEY environment variable not set")
        print("\nTo get an API key:")
        print("1. Sign up at https://together.ai")
        print("2. Get your API key from the dashboard")
        print("3. Export it: export TOGETHER_API_KEY='your-key'")
        return False
    return True


def main():
    """Run verification using Together AI models."""
    print("MAVEN - Together AI Example")
    print("=" * 60)

    if not check_api_key():
        return

    # Option 1: Use model aliases (simplest)
    # These are short names that map to full Together AI model paths
    orchestrator = ConsensusOrchestrator(
        models=[
            "together/llama-3.3-70b",
            "together/mixtral-8x22b",
            "together/qwen-2.5-72b",
        ],
        config={
            "max_iterations": 3,
            "consensus_threshold": 0.75,
        },
    )

    query = "What is the capital of Japan and what is it known for?"

    print(f"\nQuery: {query}")
    print(f"Models: Llama 3.3 70B, Mixtral 8x22B, Qwen 2.5 72B")
    print("-" * 60)
    print("Running verification...")

    result = orchestrator.verify(query)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"\nConsensus: {result.consensus}")
    print(f"Confidence: {result.confidence:.1f}%")
    print(f"Iterations: {result.iterations}")

    if result.dissent:
        print(f"Dissent: {result.dissent}")


def example_with_full_paths():
    """Example using full Together AI model paths."""
    print("\nMAVEN - Together AI with Full Model Paths")
    print("=" * 60)

    if not check_api_key():
        return

    # Option 2: Use full model paths directly
    orchestrator = ConsensusOrchestrator(
        models=[
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "mistralai/Mixtral-8x22B-Instruct-v0.1",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
        ],
    )

    result = orchestrator.verify("What programming language was Python named after?")

    print(f"\nConsensus: {result.consensus}")
    print(f"Confidence: {result.confidence:.1f}%")


def example_cost_effective():
    """Example using smaller, more cost-effective models."""
    print("\nMAVEN - Cost-Effective Together AI Setup")
    print("=" * 60)

    if not check_api_key():
        return

    # Use smaller models for lower costs
    orchestrator = ConsensusOrchestrator(
        models=[
            "together/llama-3.1-8b",
            "together/qwen-2.5-7b",
            "together/mixtral-8x7b",
        ],
        config={
            "max_iterations": 2,  # Fewer iterations
        },
    )

    result = orchestrator.verify("What is 2 + 2?")

    print(f"\nConsensus: {result.consensus}")
    print(f"Confidence: {result.confidence:.1f}%")


def list_available_models():
    """Print available Together AI model aliases."""
    from maven.models import TOGETHER_MODEL_ALIASES

    print("\nAvailable Together AI Model Aliases")
    print("=" * 60)
    print("\nUse these with 'together/' prefix or directly:")
    print()

    for alias, full_path in sorted(TOGETHER_MODEL_ALIASES.items()):
        print(f"  {alias:20} -> {full_path}")

    print("\nExample usage:")
    print('  models=["together/llama-3.3-70b", "together/mixtral-8x22b", ...]')


if __name__ == "__main__":
    list_available_models()
    print()
    main()
