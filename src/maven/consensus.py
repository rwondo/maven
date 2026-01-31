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
            all_claims.append((response.model, claims))

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(all_claims)):
            for j in range(i + 1, len(all_claims)):
                sim = calculate_similarity(all_claims[i][1], all_claims[j][1])
                similarities.append((all_claims[i][0], all_claims[j][0], sim))

        if not similarities:
            return False, 0.0, None

        # Average similarity as confidence score
        avg_similarity = sum(s[2] for s in similarities) / len(similarities)
        confidence = avg_similarity * 100  # Convert to percentage

        # Check for consensus
        if avg_similarity >= self.threshold:
            # Full consensus
            return True, confidence, None

        # Check for 2/3 consensus
        if len(responses) >= 3:
            # Find if any two models agree strongly
            for model_a, model_b, sim in similarities:
                if sim >= self.threshold:
                    # Find the dissenting model
                    agreeing = {model_a, model_b}
                    for response in responses:
                        if response.model not in agreeing:
                            return True, confidence, f"Dissent from {response.model}"

        return False, confidence, None

    def extract_consensus_answer(self, responses: List[ModelResponse]) -> str:
        """Extract the consensus answer from responses.

        Uses the mediator's proposed consensus if available,
        otherwise synthesizes from all responses.

        Args:
            responses: List of model responses.

        Returns:
            The consensus answer string.
        """
        # Look for mediator response first
        for response in responses:
            if response.role.lower() == "mediator":
                # Try to extract PROPOSED CONSENSUS section
                content = response.content
                if "PROPOSED CONSENSUS:" in content:
                    idx = content.index("PROPOSED CONSENSUS:")
                    consensus_section = content[idx + len("PROPOSED CONSENSUS:"):].strip()
                    # Take until next section or end
                    for marker in ["CONFIDENCE:", "\n\n"]:
                        if marker in consensus_section:
                            consensus_section = consensus_section.split(marker)[0].strip()
                    return consensus_section

        # Fallback: use architect's answer
        for response in responses:
            if response.role.lower() == "architect":
                content = response.content
                if "ANSWER:" in content:
                    idx = content.index("ANSWER:")
                    answer_section = content[idx + len("ANSWER:"):].strip()
                    for marker in ["REASONING:", "\n\n"]:
                        if marker in answer_section:
                            answer_section = answer_section.split(marker)[0].strip()
                    return answer_section

        # Last resort: return first response content
        if responses:
            return responses[0].content

        return "No consensus reached"
