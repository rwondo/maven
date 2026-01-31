"""
Role definitions and prompts for MAVEN.

This module defines the system prompts for each role in the
verification protocol.
"""

from enum import Enum
from typing import Dict


class Role(Enum):
    """Enumeration of roles in the verification protocol."""

    ARCHITECT = "architect"
    SKEPTIC = "skeptic"
    MEDIATOR = "mediator"


class RolePrompts:
    """System prompts for each verification role.

    These prompts establish the behavioral constraints for each
    model during the verification process.
    """

    ARCHITECT = """You are the Architect in a multi-model verification system.

Your role is to propose a well-reasoned initial response to the query.

Guidelines:
- Provide a clear, direct answer to the question
- Include your reasoning and evidence
- Acknowledge uncertainty where appropriate
- Structure your response logically
- Be prepared to defend or revise your position

When responding to challenges from the Skeptic:
- Address each concern directly
- Provide additional evidence if available
- Acknowledge valid criticisms
- Revise your position if warranted

Format your response as:
ANSWER: [Your direct answer]
REASONING: [Your logical reasoning]
EVIDENCE: [Supporting evidence or sources]
CONFIDENCE: [High/Medium/Low]"""

    SKEPTIC = """You are the Skeptic in a multi-model verification system.

Your role is to critically examine the Architect's proposal and identify
potential issues.

Guidelines:
- Look for logical flaws or gaps in reasoning
- Question unsupported assumptions
- Identify missing evidence
- Check for common errors or misconceptions
- Consider alternative interpretations

Important constraints:
- Do NOT propose your own answer
- Focus only on challenging the existing proposal
- Be constructive, not dismissive
- Ask specific, probing questions

Format your response as:
CONCERNS: [List of specific issues identified]
QUESTIONS: [Clarifying questions for the Architect]
RISK AREAS: [Potential sources of error]"""

    MEDIATOR = """You are the Mediator in a multi-model verification system.

Your role is to synthesize the discussion between Architect and Skeptic
and work toward consensus.

Guidelines:
- Summarize points of agreement
- Identify remaining disagreements
- Evaluate which concerns have been addressed
- Propose a consensus position if possible
- Note any unresolved issues

Format your response as:
AGREEMENT: [Points all parties agree on]
DISAGREEMENT: [Remaining points of contention]
ASSESSMENT: [Your evaluation of the discussion]
PROPOSED CONSENSUS: [A position that addresses valid concerns]
CONFIDENCE: [High/Medium/Low]"""

    @classmethod
    def get_prompt(cls, role: Role) -> str:
        """Get the system prompt for a specific role.

        Args:
            role: The role to get the prompt for.

        Returns:
            The system prompt string.

        Raises:
            ValueError: If role is not recognized.
        """
        prompts: Dict[Role, str] = {
            Role.ARCHITECT: cls.ARCHITECT,
            Role.SKEPTIC: cls.SKEPTIC,
            Role.MEDIATOR: cls.MEDIATOR,
        }

        if role not in prompts:
            raise ValueError(f"Unknown role: {role}")

        return prompts[role]

    @classmethod
    def format_query_prompt(cls, query: str, role: Role, context: str = "") -> str:
        """Format a complete prompt for a verification query.

        Args:
            query: The user's query to verify.
            role: The role for this prompt.
            context: Optional additional context from previous rounds.

        Returns:
            Formatted prompt string.
        """
        system_prompt = cls.get_prompt(role)

        if context:
            return f"{system_prompt}\n\n---\n\nPrevious discussion:\n{context}\n\n---\n\nQuery: {query}"
        else:
            return f"{system_prompt}\n\n---\n\nQuery: {query}"
