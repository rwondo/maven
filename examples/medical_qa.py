"""
Medical question-answering example using MAVEN.

This example demonstrates using MAVEN for medical information
synthesis, where accuracy is critical.

DISCLAIMER: This is for educational/research purposes only.
MAVEN is not a substitute for professional medical advice.

Usage:
    python medical_qa.py

Requirements:
    - ANTHROPIC_API_KEY environment variable
    - OPENAI_API_KEY environment variable
    - GOOGLE_API_KEY environment variable
"""

from maven import ConsensusOrchestrator


DISCLAIMER = """
IMPORTANT DISCLAIMER:
This example is for educational and research purposes only.
The output should NOT be used for actual medical decisions.
Always consult qualified healthcare professionals.
"""


def main():
    """Run medical Q&A example with high verification standards."""
    print("MAVEN - Medical Information Synthesis Example")
    print("=" * 60)
    print(DISCLAIMER)
    print("=" * 60)

    orchestrator = ConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"],
        config={
            "max_iterations": 5,  # More iterations for medical topics
            "consensus_threshold": 0.85,  # Higher threshold for accuracy
        },
    )

    # Example medical question
    query = """What are the common drug interactions to be aware of
when a patient is taking warfarin (a blood thinner)?

Please provide:
1. Major drug classes that interact with warfarin
2. Common foods that affect warfarin
3. Why these interactions occur
4. General guidance on monitoring

Note: This is for educational purposes only."""

    print(f"\nQuery: {query[:100]}...")
    print("-" * 60)
    print("Running multi-model verification...")

    result = orchestrator.verify(query)

    print("\n" + "=" * 60)
    print("Verified Medical Information")
    print("=" * 60)

    print(f"\n{result.consensus}")

    print("\n" + "-" * 60)
    print(f"Verification Confidence: {result.confidence:.1f}%")
    print(f"Consensus Rounds: {result.iterations}")

    if result.dissent:
        print(f"\nImportant Note: {result.dissent}")

    # Show verification summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    iteration_count = max(step.iteration for step in result.trace)
    for i in range(1, iteration_count + 1):
        iteration_steps = [s for s in result.trace if s.iteration == i]
        roles_in_round = [s.role for s in iteration_steps]
        print(f"  Round {i}: {', '.join(roles_in_round)}")

    print(DISCLAIMER)


def verify_medical_claim(claim: str) -> dict:
    """Verify a specific medical claim.

    Args:
        claim: The medical claim to verify.

    Returns:
        Dictionary with verification results.
    """
    orchestrator = ConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"],
        config={
            "max_iterations": 4,
            "consensus_threshold": 0.85,
        },
    )

    query = f"""Evaluate the accuracy of this medical claim:

"{claim}"

Assess:
1. Is this claim accurate, partially accurate, or inaccurate?
2. What is the scientific basis?
3. Are there important nuances or exceptions?
4. What sources support or contradict this?

Note: Educational purposes only."""

    result = orchestrator.verify(query)

    return {
        "claim": claim,
        "assessment": result.consensus,
        "confidence": result.confidence,
        "iterations": result.iterations,
        "has_dissent": result.dissent is not None,
    }


if __name__ == "__main__":
    main()
