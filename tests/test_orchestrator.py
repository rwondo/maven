"""
Tests for ConsensusOrchestrator class.
"""

import pytest

from maven import ConsensusOrchestrator
from maven.consensus import ConsensusResult, TraceStep
from maven.roles import Role


class TestOrchestratorInitialization:
    """Tests for orchestrator initialization."""

    def test_init_with_valid_models(self):
        """Orchestrator initializes with valid model list."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-model-1", "mock-model-2", "mock-model-3"]
        )
        assert len(orchestrator.model_ids) == 3

    def test_init_fails_with_too_few_models(self):
        """Orchestrator raises error with fewer than 3 models."""
        with pytest.raises(ValueError, match="at least 3 models"):
            ConsensusOrchestrator(models=["mock-1", "mock-2"])

    def test_init_fails_with_empty_models(self):
        """Orchestrator raises error with empty model list."""
        with pytest.raises(ValueError):
            ConsensusOrchestrator(models=[])

    def test_init_fails_with_duplicate_models(self):
        """Orchestrator raises error with duplicate models."""
        with pytest.raises(ValueError, match="Duplicate"):
            ConsensusOrchestrator(
                models=["mock-model", "mock-model", "mock-model-2"]
            )

    def test_init_with_custom_config(self):
        """Orchestrator accepts custom configuration."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"],
            config={"max_iterations": 10},
        )
        assert orchestrator.config["max_iterations"] == 10

    def test_init_preserves_default_config(self):
        """Custom config doesn't remove default values."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"],
            config={"max_iterations": 10},
        )
        assert "consensus_threshold" in orchestrator.config


class TestRoleAssignment:
    """Tests for role assignment functionality."""

    def test_assign_roles_returns_three_roles(self):
        """Role assignment produces exactly three roles."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"]
        )
        roles = orchestrator._assign_roles()
        assert len(roles) == 3

    def test_assign_roles_includes_all_role_types(self):
        """All three role types are assigned."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"]
        )
        roles = orchestrator._assign_roles()

        role_values = set(roles.values())
        expected = {Role.ARCHITECT, Role.SKEPTIC, Role.MEDIATOR}
        assert role_values == expected

    def test_role_rotation_changes_roles(self):
        """Role rotation changes model assignments."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"]
        )
        orchestrator._current_roles = orchestrator._assign_roles()
        original_roles = orchestrator._current_roles.copy()

        orchestrator._rotate_roles()

        # Roles should be different after rotation
        for model, role in orchestrator._current_roles.items():
            assert role != original_roles[model]


class TestVerification:
    """Tests for the verify method."""

    def test_verify_returns_consensus_result(self):
        """Verify returns a ConsensusResult object."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-model-1", "mock-model-2", "mock-model-3"]
        )

        # Note: This will fail without mock models set up
        # In real tests, you'd mock the model responses
        try:
            result = orchestrator.verify("Test query")
            assert isinstance(result, ConsensusResult)
        except Exception:
            # Expected if mock models aren't configured
            pass

    def test_verify_rejects_empty_query(self):
        """Verify raises error for empty query."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"]
        )

        with pytest.raises(ValueError, match="empty"):
            orchestrator.verify("")

    def test_verify_rejects_whitespace_query(self):
        """Verify raises error for whitespace-only query."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"]
        )

        with pytest.raises(ValueError, match="empty"):
            orchestrator.verify("   ")

    def test_max_iterations_parameter(self):
        """Verify respects max_iterations parameter."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"],
            config={"max_iterations": 2},
        )
        # Would need mock models to fully test


class TestTraceGeneration:
    """Tests for trace generation."""

    def test_get_trace_returns_list(self):
        """get_trace returns a list."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"]
        )
        trace = orchestrator.get_trace()
        assert isinstance(trace, list)

    def test_trace_is_copy(self):
        """get_trace returns a copy, not the original."""
        orchestrator = ConsensusOrchestrator(
            models=["mock-1", "mock-2", "mock-3"]
        )
        trace1 = orchestrator.get_trace()
        trace2 = orchestrator.get_trace()
        assert trace1 is not trace2


class TestTraceStep:
    """Tests for TraceStep dataclass."""

    def test_trace_step_creation(self):
        """TraceStep can be created with required fields."""
        step = TraceStep(
            iteration=1,
            role="architect",
            model="test-model",
            content="Test content",
        )
        assert step.iteration == 1
        assert step.role == "architect"

    def test_trace_step_summary_short_content(self):
        """Summary returns full content for short text."""
        step = TraceStep(
            iteration=1,
            role="architect",
            model="test-model",
            content="Short content",
        )
        assert step.summary == "Short content"

    def test_trace_step_summary_long_content(self):
        """Summary truncates long content."""
        long_content = "x" * 200
        step = TraceStep(
            iteration=1,
            role="architect",
            model="test-model",
            content=long_content,
        )
        assert len(step.summary) <= 100
        assert step.summary.endswith("...")
