"""
MAVEN - Multi-Agent Verification & Evaluation Network

Production-ready hallucination detection for high-stakes domains using
multi-model verification.

Primary Use Case: Flag dangerous AI hallucinations in law, medicine, finance,
and other critical applications where errors could cause serious harm.

Key Finding: 85.3% hallucination detection rate on TruthfulQA with 82% accuracy.
Better to flag a few good answers than miss dangerous hallucinations.

v1.0 Features:
    - Hallucination Detection: Multi-model consensus for catching AI fabrications
    - Async/Parallel: Full async support for batch processing
    - Domain-Specific: Specialized prompts for medical, legal, financial domains
    - Framework Integration: LangChain and LlamaIndex support
    - MCP Support: Model Context Protocol for external tool verification

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

Async Batch Processing:
    from maven import AsyncHallucinationDetector
    import asyncio

    async def check_batch():
        detector = AsyncHallucinationDetector(models=["llama", "qwen", "mixtral"])
        reports = await detector.detect_batch([
            {"query": "Q1", "answer": "A1"},
            {"query": "Q2", "answer": "A2"},
        ], max_concurrent=5)
        return reports

LangChain Integration:
    from maven.integrations import MAVENChain, MAVENCallbackHandler

    # Callback for automatic detection
    handler = MAVENCallbackHandler(models=["llama", "qwen"])
    llm = OpenAI(callbacks=[handler])

    # Or wrap a chain
    safe_chain = MAVENChain(chain=my_chain, models=["llama", "qwen"])

LlamaIndex Integration:
    from maven.integrations import MAVENQueryEngine

    safe_engine = MAVENQueryEngine(
        query_engine=index.as_query_engine(),
        models=["llama", "qwen"]
    )
"""

__version__ = "1.0.0"  # Production-ready release
__author__ = "Arber Ferra"

# Primary API
from maven.hallucination_detector import HallucinationDetector, HallucinationReport

# MCP Server Integration
from maven.mcp_integration import (
    MCPServer,
    MCPServerRegistry,
    StdioMCPServer,
    HTTPMCPServer,
    create_mcp_server
)

# Domain-specific prompts
from maven.hallucination_detector import DOMAIN_PROMPTS

# Experimental features (consensus-based generation - not recommended)
from maven.orchestrator import ConsensusOrchestrator, VerificationOrchestrator
from maven.consensus import ConsensusResult, ConsensusDetector, VerificationResult
from maven.models import ModelInterface
from maven.roles import RolePrompts

# Async support
try:
    from maven.async_orchestrator import AsyncConsensusOrchestrator
    from maven.async_models import AsyncModelInterface
    from maven.async_hallucination_detector import AsyncHallucinationDetector
    _async_available = True
except ImportError:
    _async_available = False

# Framework integrations (optional)
try:
    from maven.integrations import (
        # LangChain
        MAVENCallbackHandler,
        MAVENChain,
        MAVENRetriever,
        # LlamaIndex
        MAVENQueryEngine,
        MAVENResponseEvaluator,
        MAVENResponse,
        # Common
        HallucinationCheckResult,
        HallucinationError,
        # Factory functions
        create_langchain_callback,
        wrap_langchain_chain,
        wrap_llamaindex_engine,
    )
    _integrations_available = True
except ImportError:
    _integrations_available = False

__all__ = [
    # Primary API (recommended)
    "HallucinationDetector",
    "HallucinationReport",
    "DOMAIN_PROMPTS",
    # MCP Server Integration
    "MCPServer",
    "MCPServerRegistry",
    "StdioMCPServer",
    "HTTPMCPServer",
    "create_mcp_server",
    # Experimental (not recommended for generation)
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
        "AsyncHallucinationDetector",
        "AsyncConsensusOrchestrator",
        "AsyncModelInterface",
    ])

if _integrations_available:
    __all__.extend([
        # LangChain
        "MAVENCallbackHandler",
        "MAVENChain",
        "MAVENRetriever",
        # LlamaIndex
        "MAVENQueryEngine",
        "MAVENResponseEvaluator",
        "MAVENResponse",
        # Common
        "HallucinationCheckResult",
        "HallucinationError",
        # Factory functions
        "create_langchain_callback",
        "wrap_langchain_chain",
        "wrap_llamaindex_engine",
    ])
