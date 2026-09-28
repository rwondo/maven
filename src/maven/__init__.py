"""MAVEN: ask several LLMs to review an answer and flag likely hallucinations.

Example:
    from maven import HallucinationDetector

    detector = HallucinationDetector(
        models=["together/llama-3.1-8b", "together/qwen-2.5-7b", "together/mixtral-8x7b"]
    )
    report = detector.detect(
        query="Who wrote Pride and Prejudice?",
        answer="Charlotte Bronte wrote it in 1847.",
    )
    print(report.risk_level, report.flags)
"""

from importlib.metadata import PackageNotFoundError, version

from maven.async_hallucination_detector import AsyncHallucinationDetector
from maven.hallucination_detector import HallucinationDetector, HallucinationReport, TraceStep
from maven.models import ModelConfigError, ModelInterface, create_model

try:
    __version__ = version("maven-ai")
except PackageNotFoundError:  # imported from a source tree that was never installed
    __version__ = "0+unknown"

__all__ = [
    "AsyncHallucinationDetector",
    "HallucinationDetector",
    "HallucinationReport",
    "ModelConfigError",
    "ModelInterface",
    "TraceStep",
    "__version__",
    "create_model",
]
