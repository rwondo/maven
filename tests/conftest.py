"""
Pytest configuration and fixtures for MAVEN tests.

This module provides reusable fixtures for testing without
making actual API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from maven.consensus import ConsensusResult, ModelResponse, TraceStep
from maven.models import MockModel

# ---------------------------------------------------------------------------
# Mock Model Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_model_ids() -> list[str]:
    """Provide standard mock model identifiers."""
    return ["mock-model-1", "mock-model-2", "mock-model-3"]


@pytest.fixture
def mock_models() -> list[MockModel]:
    """Provide configured mock model instances."""
    return [
        MockModel(
            "mock-model-1",
            responses={
                "architect": "ANSWER: Test answer\nREASONING: Test reasoning\nCONFIDENCE: High",
                "skeptic": "CONCERNS: None identified\nQUESTIONS: None",
                "mediator": "PROPOSED CONSENSUS: Test answer is correct\nCONFIDENCE: High",
            },
        ),
        MockModel(
            "mock-model-2",
            responses={
                "architect": "ANSWER: Test answer\nREASONING: Supporting logic\nCONFIDENCE: High",
                "skeptic": "CONCERNS: Minor issue\nQUESTIONS: Can you clarify?",
                "mediator": "PROPOSED CONSENSUS: Test answer confirmed\nCONFIDENCE: High",
            },
        ),
        MockModel(
            "mock-model-3",
            responses={
                "architect": "ANSWER: Test answer\nREASONING: Additional support\nCONFIDENCE: Medium",
                "skeptic": "CONCERNS: None\nQUESTIONS: None",
                "mediator": "PROPOSED CONSENSUS: Agreement on test answer\nCONFIDENCE: High",
            },
        ),
    ]


@pytest.fixture
def disagreeing_mock_models() -> list[MockModel]:
    """Provide mock models that disagree for testing dissent handling."""
    return [
        MockModel(
            "mock-model-1",
            responses={
                "architect": "ANSWER: Answer A\nREASONING: Reason A\nCONFIDENCE: High",
                "skeptic": "CONCERNS: Disagree with this\nQUESTIONS: Why not B?",
                "mediator": "PROPOSED CONSENSUS: Answer A\nCONFIDENCE: Medium",
            },
        ),
        MockModel(
            "mock-model-2",
            responses={
                "architect": "ANSWER: Answer B\nREASONING: Reason B\nCONFIDENCE: High",
                "skeptic": "CONCERNS: A is wrong\nQUESTIONS: Evidence?",
                "mediator": "PROPOSED CONSENSUS: Answer B\nCONFIDENCE: Medium",
            },
        ),
        MockModel(
            "mock-model-3",
            responses={
                "architect": "ANSWER: Answer A\nREASONING: Agree with A\nCONFIDENCE: High",
                "skeptic": "CONCERNS: B seems off\nQUESTIONS: Source?",
                "mediator": "PROPOSED CONSENSUS: Answer A with caveats\nCONFIDENCE: Low",
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Response Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_responses() -> list[ModelResponse]:
    """Provide sample model responses for testing."""
    return [
        ModelResponse(
            model="model-1",
            role="architect",
            content="ANSWER: Paris\nREASONING: Capital of France\nCONFIDENCE: High",
        ),
        ModelResponse(
            model="model-2",
            role="skeptic",
            content="CONCERNS: None\nQUESTIONS: None",
        ),
        ModelResponse(
            model="model-3",
            role="mediator",
            content="PROPOSED CONSENSUS: Paris is correct\nCONFIDENCE: High",
        ),
    ]


@pytest.fixture
def sample_trace() -> list[TraceStep]:
    """Provide sample trace steps for testing."""
    return [
        TraceStep(
            iteration=1,
            role="architect",
            model="model-1",
            content="Initial proposal",
        ),
        TraceStep(
            iteration=1,
            role="skeptic",
            model="model-2",
            content="Challenge",
        ),
        TraceStep(
            iteration=1,
            role="mediator",
            model="model-3",
            content="Synthesis",
        ),
    ]


@pytest.fixture
def sample_consensus_result(sample_trace) -> ConsensusResult:
    """Provide sample consensus result for testing."""
    return ConsensusResult(
        consensus="Paris",
        confidence=95.0,
        iterations=1,
        trace=sample_trace,
        metadata={"trace_id": "test-trace-123"},
    )


# ---------------------------------------------------------------------------
# Orchestrator Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_orchestrator(mock_model_ids):
    """Provide orchestrator with mocked model creation."""
    from maven import ConsensusOrchestrator

    with patch("maven.orchestrator.create_model") as mock_create:
        mock_create.side_effect = lambda mid: MockModel(
            mid,
            responses={
                "architect": "ANSWER: Test\nREASONING: Test\nCONFIDENCE: High",
                "skeptic": "CONCERNS: None\nQUESTIONS: None",
                "mediator": "PROPOSED CONSENSUS: Test confirmed\nCONFIDENCE: High",
            },
        )

        orchestrator = ConsensusOrchestrator(models=mock_model_ids)
        yield orchestrator


# ---------------------------------------------------------------------------
# Configuration Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_config() -> dict:
    """Provide default configuration for testing."""
    return {
        "max_iterations": 3,
        "consensus_threshold": 0.8,
        "timeout_seconds": 30,
        "enable_role_rotation": True,
        "trace_verbosity": "full",
    }


@pytest.fixture
def strict_config() -> dict:
    """Provide strict configuration requiring high consensus."""
    return {
        "max_iterations": 5,
        "consensus_threshold": 0.95,
        "timeout_seconds": 60,
        "enable_role_rotation": True,
    }


# ---------------------------------------------------------------------------
# API Mock Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client."""
    with patch("anthropic.Anthropic") as mock:
        client = MagicMock()
        mock.return_value = client

        # Configure mock response
        message = MagicMock()
        message.content = [MagicMock(text="Mock Claude response")]
        client.messages.create.return_value = message

        yield client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI API client."""
    with patch("openai.OpenAI") as mock:
        client = MagicMock()
        mock.return_value = client

        # Configure mock response
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content="Mock GPT response"))]
        client.chat.completions.create.return_value = response

        yield client


@pytest.fixture
def mock_gemini_model():
    """Mock Google Gemini model."""
    with patch("google.generativeai.GenerativeModel") as mock:
        model = MagicMock()
        mock.return_value = model

        # Configure mock response
        response = MagicMock()
        response.text = "Mock Gemini response"
        model.generate_content.return_value = response

        yield model


# ---------------------------------------------------------------------------
# Environment Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set mock environment variables for API keys."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")


# ---------------------------------------------------------------------------
# Utility Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_queries() -> list[str]:
    """Provide sample test queries."""
    return [
        "What is the capital of France?",
        "What is 2 + 2?",
        "Who wrote Romeo and Juliet?",
        "What is the boiling point of water?",
    ]
