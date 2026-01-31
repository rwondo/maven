"""
Tests for role definitions and prompts.
"""

import pytest

from maven.roles import Role, RolePrompts


class TestRoleEnum:
    """Tests for Role enumeration."""

    def test_role_values(self):
        """Role enum has expected values."""
        assert Role.ARCHITECT.value == "architect"
        assert Role.SKEPTIC.value == "skeptic"
        assert Role.MEDIATOR.value == "mediator"

    def test_role_count(self):
        """There are exactly three roles."""
        assert len(Role) == 3


class TestRolePrompts:
    """Tests for RolePrompts class."""

    def test_architect_prompt_exists(self):
        """Architect prompt is defined."""
        assert RolePrompts.ARCHITECT is not None
        assert len(RolePrompts.ARCHITECT) > 100

    def test_skeptic_prompt_exists(self):
        """Skeptic prompt is defined."""
        assert RolePrompts.SKEPTIC is not None
        assert len(RolePrompts.SKEPTIC) > 100

    def test_mediator_prompt_exists(self):
        """Mediator prompt is defined."""
        assert RolePrompts.MEDIATOR is not None
        assert len(RolePrompts.MEDIATOR) > 100

    def test_architect_prompt_content(self):
        """Architect prompt contains key instructions."""
        prompt = RolePrompts.ARCHITECT
        assert "Architect" in prompt
        assert "propose" in prompt.lower() or "initial" in prompt.lower()

    def test_skeptic_prompt_content(self):
        """Skeptic prompt contains key instructions."""
        prompt = RolePrompts.SKEPTIC
        assert "Skeptic" in prompt
        assert "challenge" in prompt.lower() or "question" in prompt.lower()

    def test_mediator_prompt_content(self):
        """Mediator prompt contains key instructions."""
        prompt = RolePrompts.MEDIATOR
        assert "Mediator" in prompt
        assert "consensus" in prompt.lower() or "synthesize" in prompt.lower()

    def test_get_prompt_architect(self):
        """get_prompt returns architect prompt."""
        prompt = RolePrompts.get_prompt(Role.ARCHITECT)
        assert prompt == RolePrompts.ARCHITECT

    def test_get_prompt_skeptic(self):
        """get_prompt returns skeptic prompt."""
        prompt = RolePrompts.get_prompt(Role.SKEPTIC)
        assert prompt == RolePrompts.SKEPTIC

    def test_get_prompt_mediator(self):
        """get_prompt returns mediator prompt."""
        prompt = RolePrompts.get_prompt(Role.MEDIATOR)
        assert prompt == RolePrompts.MEDIATOR


class TestPromptFormatting:
    """Tests for prompt formatting functions."""

    def test_format_query_prompt_basic(self):
        """format_query_prompt creates valid prompt."""
        query = "What is 2 + 2?"
        prompt = RolePrompts.format_query_prompt(query, Role.ARCHITECT)

        assert "What is 2 + 2?" in prompt
        assert "Architect" in prompt

    def test_format_query_prompt_with_context(self):
        """format_query_prompt includes context when provided."""
        query = "What is the answer?"
        context = "Previous discussion about mathematics."
        prompt = RolePrompts.format_query_prompt(query, Role.SKEPTIC, context)

        assert query in prompt
        assert context in prompt

    def test_format_query_prompt_without_context(self):
        """format_query_prompt works without context."""
        query = "Test query"
        prompt = RolePrompts.format_query_prompt(query, Role.MEDIATOR)

        assert query in prompt
        assert "Previous discussion" not in prompt

    def test_format_query_includes_role_prompt(self):
        """Formatted prompt includes the role's system prompt."""
        query = "Test"
        prompt = RolePrompts.format_query_prompt(query, Role.ARCHITECT)

        # Should contain architect-specific instructions
        assert "ANSWER:" in prompt or "well-reasoned" in prompt.lower()


class TestPromptStructure:
    """Tests for prompt structure and formatting."""

    def test_prompts_have_format_instructions(self):
        """All prompts include output format instructions."""
        for role in Role:
            prompt = RolePrompts.get_prompt(role)
            # Each prompt should mention format
            assert "Format" in prompt or ":" in prompt

    def test_architect_has_answer_format(self):
        """Architect prompt specifies ANSWER format."""
        assert "ANSWER:" in RolePrompts.ARCHITECT

    def test_skeptic_has_concerns_format(self):
        """Skeptic prompt specifies CONCERNS format."""
        assert "CONCERNS:" in RolePrompts.SKEPTIC

    def test_mediator_has_consensus_format(self):
        """Mediator prompt specifies PROPOSED CONSENSUS format."""
        assert "PROPOSED CONSENSUS:" in RolePrompts.MEDIATOR
