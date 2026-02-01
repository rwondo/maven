"""
MAVEN - Multi-Agent Verification & Evaluation Network

Hallucination detection for high-stakes domains using multi-model verification.

Primary Use Case: Flag dangerous AI hallucinations in law, medicine, and other
critical applications where errors could cause serious harm.

Key Finding: Perfect detection of critical hallucinations (100%) with acceptable
over-flagging of safe content. Better to flag 3 good answers than miss 1 dangerous one.

Basic Usage:
    from maven import HallucinationDetector

    detector = HallucinationDetector(
        models=["together/llama-3.1-8b", "together/qwen-2.5-7b", "together/mixtral-8x7b"]
    )

    # Check an AI-generated answer for hallucinations
    report = detector.detect(
        query="What are contraindications for aspirin?",
        answer="According to the 2023 Johnson Study, aspirin causes...",
        domain="medical"
    )

    print(f"Risk Level: {report.risk_level}")  # LOW, MEDIUM, HIGH, or CRITICAL
    print(f"Confidence: {report.confidence_score}%")
    print(f"Flags: {report.flags}")

    # In production: Block or warn on CRITICAL/HIGH risk responses

Experimental Features (not recommended for production):
    - ConsensusOrchestrator: Multi-agent consensus (performs worse than single model)
    - VerificationOrchestrator: Propose-verify protocol (no improvement over baseline)
    - CollaborativeOrchestrator: Collaborative reasoning (67% vs 100% baseline)

    Benchmark Results: Single models outperformed all multi-agent approaches on
    accuracy tasks. Multi-agent value is in hallucination DETECTION, not generation.
"""

__version__ = "0.2.0"  # Updated for hallucination detection focus
__author__ = "Arber Ferra"

# Primary API
from maven.hallucination_detector import HallucinationDetector, HallucinationReport

# Experimental/deprecated features
from maven.orchestrator import ConsensusOrchestrator, VerificationOrchestrator
from maven.consensus import ConsensusResult, ConsensusDetector, VerificationResult
from maven.models import ModelInterface
from maven.roles import RolePrompts

# Async imports (optional)
try:
    from maven.async_orchestrator import AsyncConsensusOrchestrator
    from maven.async_models import AsyncModelInterface
    _async_available = True
except ImportError:
    _async_available = False

__all__ = [
    # Primary API (recommended)
    "HallucinationDetector",
    "HallucinationReport",
    # Experimental (not recommended)
    "ConsensusOrchestrator",
    "VerificationOrchestrator",
    "ConsensusResult",
    "VerificationResult",
    "ConsensusDetector",
    # Common exports
    "ModelInterface",
    "RolePrompts",
    "__version__",
]

if _async_available:
    __all__.extend([
        "AsyncConsensusOrchestrator",
        "AsyncModelInterface",
    ])
