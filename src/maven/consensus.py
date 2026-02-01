"""
Consensus detection logic for MAVEN.

This module determines when models have reached agreement.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from maven.utils import (
    calculate_similarity,
    extract_key_claims,
    extract_structured_answer,
    get_timestamp,
)

logger = logging.getLogger(__name__)


@dataclass
class TraceStep:
    """A single step in the verification trace."""

    iteration: int
    role: str
    model: str
    content: str
    timestamp: str = field(default_factory=get_timestamp)

    @property
    def summary(self) -> str:
        """Get a brief summary of this step."""
        max_len = 100
        if len(self.content) <= max_len:
            return self.content
        return self.content[:max_len - 3] + "..."


@dataclass
class ConsensusResult:
    """Result of a verification process."""

    consensus: str
    confidence: float
    iterations: int
    trace: List[TraceStep]
    dissent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "consensus": self.consensus,
            "confidence": self.confidence,
            "iterations": self.iterations,
            "trace": [
                {
                    "iteration": step.iteration,
                    "role": step.role,
                    "model": step.model,
                    "content": step.content,
                    "timestamp": step.timestamp,
                }
                for step in self.trace
            ],
            "dissent": self.dissent,
            "metadata": self.metadata,
        }


@dataclass
class VerificationResult:
    """Result of a verification process (new protocol)."""

    verdict: str  # "ACCEPTED", "REJECTED", "UNCERTAIN"
    answer: str  # The final answer
    errors: List[str]  # List of errors found, empty if accepted
    confidence: float  # 0-100
    trace: List[TraceStep]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "verdict": self.verdict,
            "answer": self.answer,
            "errors": self.errors,
            "confidence": self.confidence,
            "trace": [
                {
                    "iteration": step.iteration,
                    "role": step.role,
                    "model": step.model,
                    "content": step.content,
                    "timestamp": step.timestamp,
                }
                for step in self.trace
            ],
            "metadata": self.metadata,
        }


@dataclass
class ModelResponse:
    """Response from a model during verification."""

    model: str
    role: str
    content: str
    timestamp: str = field(default_factory=get_timestamp)


class ConsensusDetector:
    """Determines when consensus has been reached among models."""

    def __init__(self, threshold: float = 0.8):
        """Initialize consensus detector.

        Args:
            threshold: Minimum agreement score for consensus (0.0-1.0).
        """
        self.threshold = threshold

    def check_consensus(
        self,
        responses: List[ModelResponse],
    ) -> tuple[bool, float, Optional[str]]:
        """Check if responses have reached consensus.

        Uses enhanced similarity calculation that prioritizes:
        - Structured answer extraction (ANSWER:, PROPOSED CONSENSUS:)
        - Numerical value comparison
        - Semantic text similarity

        Args:
            responses: List of model responses to analyze.

        Returns:
            Tuple of (consensus_reached, confidence_score, dissent_text).
        """
        if len(responses) < 2:
            logger.warning("Not enough responses for consensus check")
            return False, 0.0, None

        # Extract claims from each response
        all_claims = []
        for response in responses:
            claims = extract_key_claims(response.content)
            all_claims.append((response.model, response.role, claims))
            logger.debug(f"Extracted {len(claims)} claims from {response.model} ({response.role})")

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(all_claims)):
            for j in range(i + 1, len(all_claims)):
                sim = calculate_similarity(all_claims[i][2], all_claims[j][2])
                similarities.append((all_claims[i][0], all_claims[j][0], sim))
                logger.debug(f"Similarity between {all_claims[i][0]} and {all_claims[j][0]}: {sim:.2f}")

        if not similarities:
            return False, 0.0, None

        # Average similarity as confidence score
        avg_similarity = sum(s[2] for s in similarities) / len(similarities)
        confidence = avg_similarity * 100  # Convert to percentage

        logger.info(f"Average similarity: {avg_similarity:.2f} (confidence: {confidence:.1f}%)")

        # Check for consensus
        if avg_similarity >= self.threshold:
            # Full consensus
            logger.info("Full consensus reached")
            return True, confidence, None

        # Check for 2/3 consensus (partial agreement)
        if len(responses) >= 3:
            # Find if any two models agree strongly
            for model_a, model_b, sim in similarities:
                if sim >= self.threshold:
                    # Find the dissenting model
                    agreeing = {model_a, model_b}
                    for response in responses:
                        if response.model not in agreeing:
                            logger.info(f"Partial consensus: {model_a} and {model_b} agree, {response.model} dissents")
                            return True, confidence, f"Dissent from {response.model}"

        logger.info("No consensus reached yet")
        return False, confidence, None

    def extract_consensus_answer(self, responses: List[ModelResponse]) -> str:
        """Extract the consensus answer from responses.

        Uses enhanced structured answer extraction that prioritizes:
        1. Mediator's proposed consensus
        2. Architect's answer
        3. Any structured answer from responses
        4. First response content as fallback

        Args:
            responses: List of model responses.

        Returns:
            The consensus answer string.
        """
        # Priority 1: Look for mediator response
        for response in responses:
            if response.role.lower() == "mediator":
                structured = extract_structured_answer(response.content)
                if structured:
                    logger.debug(f"Using mediator's consensus: {structured[:100]}...")
                    return structured

        # Priority 2: Look for architect's answer
        for response in responses:
            if response.role.lower() == "architect":
                structured = extract_structured_answer(response.content)
                if structured:
                    logger.debug(f"Using architect's answer: {structured[:100]}...")
                    return structured

        # Priority 3: Extract structured answer from any response
        for response in responses:
            structured = extract_structured_answer(response.content)
            if structured:
                logger.debug(f"Using structured answer from {response.role}: {structured[:100]}...")
                return structured

        # Last resort: return first response content
        if responses:
            logger.warning("No structured answer found, using raw first response")
            return responses[0].content

        return "No consensus reached"
