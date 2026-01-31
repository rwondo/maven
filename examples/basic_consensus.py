"""
Basic consensus example: Verify a simple factual claim.

This example demonstrates the core MAVEN workflow for verifying
a straightforward factual question.

Usage:
    python basic_consensus.py

Requirements:
    - ANTHROPIC_API_KEY environment variable
    - OPENAI_API_KEY environment variable
    - GOOGLE_API_KEY environment variable
"""

from maven import ConsensusOrchestrator


def main():
    """Run a basic verification example."""
    print("MAVEN - Basic Consensus Example")
    print("=" * 50)

    # Initialize with three models
    orchestrator = ConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"],
        config={
            "max_iterations": 3,
            "consensus_threshold": 0.8,
        },
    )

    # Verify a factual claim
    query = "What is the boiling point of water at sea level in Celsius?"

    print(f"\nQuery: {query}")
    print("-" * 50)

    result = orchestrator.verify(query)

    # Display results
    print(f"\nConsensus Answer: {result.consensus}")
    print(f"Confidence: {result.confidence:.1f}%")
    print(f"Iterations: {result.iterations}")

    if result.dissent:
        print(f"Dissent: {result.dissent}")

    # Print verification trace
    print("\n" + "=" * 50)
    print("Verification Trace:")
    print("=" * 50)

    for step in result.trace:
        print(f"\n[Iteration {step.iteration}] {step.role.upper()} ({step.model})")
        print("-" * 40)
        print(step.summary)


def run_multiple_queries():
    """Run verification on multiple queries to demonstrate consistency."""
    print("\nMAVEN - Multiple Query Example")
    print("=" * 50)

    orchestrator = ConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
    )

    queries = [
        "What is the capital of Japan?",
        "How many planets are in our solar system?",
        "What year did World War II end?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        result = orchestrator.verify(query, max_iterations=2)
        print(f"Answer: {result.consensus}")
        print(f"Confidence: {result.confidence:.1f}%")


if __name__ == "__main__":
    main()
