"""
Tests for consensus detection logic.
"""

import pytest

from maven.consensus import (
    ConsensusDetector,
    ConsensusResult,
    ModelResponse,
    TraceStep,
)


class TestConsensusDetector:
    """Tests for ConsensusDetector class."""

    def test_init_default_threshold(self):
        """Detector initializes with default threshold."""
        detector = ConsensusDetector()
        assert detector.threshold == 0.8

    def test_init_custom_threshold(self):
        """Detector accepts custom threshold."""
        detector = ConsensusDetector(threshold=0.9)
        assert detector.threshold == 0.9

    def test_check_consensus_insufficient_responses(self):
        """Returns no consensus with fewer than 2 responses."""
        detector = ConsensusDetector()
        responses = [
            ModelResponse(model="m1", role="architect", content="Answer")
        ]

        reached, confidence, dissent = detector.check_consensus(responses)

        assert reached is False
        assert confidence == 0.0

    def test_check_consensus_identical_responses(self):
        """Identical responses should reach consensus."""
        detector = ConsensusDetector(threshold=0.5)
        responses = [
            ModelResponse(model="m1", role="architect", content="The answer is 42."),
            ModelResponse(model="m2", role="skeptic", content="The answer is 42."),
            ModelResponse(model="m3", role="mediator", content="The answer is 42."),
        ]

        reached, confidence, dissent = detector.check_consensus(responses)

        assert reached is True
        assert confidence > 0

    def test_check_consensus_different_responses(self):
        """Very different responses should not reach consensus."""
        detector = ConsensusDetector(threshold=0.9)
        responses = [
            ModelResponse(model="m1", role="architect", content="Apples are red fruit."),
            ModelResponse(model="m2", role="skeptic", content="The sky is blue today."),
            ModelResponse(model="m3", role="mediator", content="Cars have four wheels."),
        ]

        reached, confidence, dissent = detector.check_consensus(responses)

        assert reached is False

    def test_extract_consensus_from_mediator(self):
        """Extract consensus prioritizes mediator response."""
        detector = ConsensusDetector()
        responses = [
            ModelResponse(
                model="m1",
                role="architect",
                content="ANSWER: 42\nREASONING: Because.",
            ),
            ModelResponse(
                model="m2",
                role="skeptic",
                content="CONCERNS: None",
            ),
            ModelResponse(
                model="m3",
                role="mediator",
                content="PROPOSED CONSENSUS: The answer is definitely 42.\nCONFIDENCE: High",
            ),
        ]

        answer = detector.extract_consensus_answer(responses)

        assert "42" in answer

    def test_extract_consensus_fallback_to_architect(self):
        """Falls back to architect if no mediator consensus section."""
        detector = ConsensusDetector()
        responses = [
            ModelResponse(
                model="m1",
                role="architect",
                content="ANSWER: Paris\nREASONING: It is the capital.",
            ),
            ModelResponse(
                model="m2",
                role="skeptic",
                content="No issues found.",
            ),
        ]

        answer = detector.extract_consensus_answer(responses)

        assert "Paris" in answer


class TestConsensusResult:
    """Tests for ConsensusResult dataclass."""

    def test_result_creation(self):
        """ConsensusResult can be created with required fields."""
        result = ConsensusResult(
            consensus="Test answer",
            confidence=95.0,
            iterations=2,
            trace=[],
        )
        assert result.consensus == "Test answer"
        assert result.confidence == 95.0
        assert result.iterations == 2

    def test_result_with_dissent(self):
        """ConsensusResult can include dissent."""
        result = ConsensusResult(
            consensus="Majority answer",
            confidence=75.0,
            iterations=3,
            trace=[],
            dissent="Model X disagreed",
        )
        assert result.dissent == "Model X disagreed"

    def test_result_to_dict(self):
        """ConsensusResult converts to dictionary."""
        trace = [
            TraceStep(iteration=1, role="architect", model="m1", content="Test")
        ]
        result = ConsensusResult(
            consensus="Answer",
            confidence=90.0,
            iterations=1,
            trace=trace,
        )

        result_dict = result.to_dict()

        assert result_dict["consensus"] == "Answer"
        assert result_dict["confidence"] == 90.0
        assert len(result_dict["trace"]) == 1

    def test_result_metadata(self):
        """ConsensusResult includes metadata."""
        result = ConsensusResult(
            consensus="Answer",
            confidence=90.0,
            iterations=1,
            trace=[],
            metadata={"trace_id": "abc123"},
        )
        assert result.metadata["trace_id"] == "abc123"


class TestModelResponse:
    """Tests for ModelResponse dataclass."""

    def test_response_creation(self):
        """ModelResponse can be created."""
        response = ModelResponse(
            model="test-model",
            role="architect",
            content="Test content",
        )
        assert response.model == "test-model"
        assert response.role == "architect"
        assert response.content == "Test content"

    def test_response_has_timestamp(self):
        """ModelResponse automatically gets timestamp."""
        response = ModelResponse(
            model="test-model",
            role="architect",
            content="Test",
        )
        assert response.timestamp is not None
