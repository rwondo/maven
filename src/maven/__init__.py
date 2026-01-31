"""
MAVEN - Multi-Agent Verification & Evaluation Network

A protocol for reducing AI hallucinations through multi-model
adversarial consensus.

Basic usage:
    from maven import ConsensusOrchestrator

    orchestrator = ConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
    )
    result = orchestrator.verify("What is the speed of light?")
    print(result.consensus)

Async usage:
    from maven import AsyncConsensusOrchestrator

    orchestrator = AsyncConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
    )
    result = await orchestrator.verify("What is the speed of light?")
    print(result.consensus)
"""

__version__ = "0.1.0"
__author__ = "Arber Ferra"

from maven.orchestrator import ConsensusOrchestrator
from maven.consensus import ConsensusResult, ConsensusDetector
from maven.models import ModelInterface
from maven.roles import RolePrompts

# Async imports (optional - may not be needed in all environments)
try:
    from maven.async_orchestrator import AsyncConsensusOrchestrator
    from maven.async_models import AsyncModelInterface
    _async_available = True
except ImportError:
    _async_available = False

__all__ = [
    "ConsensusOrchestrator",
    "ConsensusResult",
    "ConsensusDetector",
    "ModelInterface",
    "RolePrompts",
    "__version__",
]

if _async_available:
    __all__.extend([
        "AsyncConsensusOrchestrator",
        "AsyncModelInterface",
    ])
