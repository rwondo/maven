"""
Core orchestration logic for MAVEN.

This module contains the main ConsensusOrchestrator class that
coordinates multi-model verification.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from maven.consensus import (
    ConsensusDetector,
    ConsensusResult,
    ModelResponse,
    TraceStep,
    VerificationResult,
)
from maven.models import ModelInterface, create_model
from maven.roles import Role, RolePrompts
from maven.tools import extract_tool_calls, execute_tool_calls, default_registry
from maven.utils import (
    DEFAULT_CONFIG,
    generate_trace_id,
    get_timestamp,
    merge_configs,
    validate_models,
)

logger = logging.getLogger(__name__)


class ConsensusOrchestrator:
    """Main orchestration class for multi-model verification.

    Coordinates three or more models in adversarial roles to achieve
    consensus on queries through iterative verification rounds.

    Example:
        >>> orchestrator = ConsensusOrchestrator(
        ...     models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
        ... )
        >>> result = orchestrator.verify("What is the capital of France?")
        >>> print(result.consensus)
        Paris
    """

    def __init__(
        self,
        models: List[str],
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize orchestrator with model list and configuration.

        Args:
            models: List of model identifiers (minimum 3 required).
            config: Optional configuration dictionary.

        Raises:
            ValueError: If fewer than 3 models provided or invalid config.
        """
        validate_models(models)

        self.model_ids = models
        self.config = merge_configs(DEFAULT_CONFIG, config)
        self._models: Dict[str, ModelInterface] = {}
        self._trace: List[TraceStep] = []
        self._current_roles: Dict[str, Role] = {}

        logger.info(f"Initialized ConsensusOrchestrator with {len(models)} models")

    def _get_model(self, model_id: str) -> ModelInterface:
        """Get or create model instance.

        Args:
            model_id: Model identifier.

        Returns:
            ModelInterface instance.
        """
        if model_id not in self._models:
            self._models[model_id] = create_model(model_id)
        return self._models[model_id]

    def _assign_roles(self) -> Dict[str, Role]:
        """Randomly assign Architect/Skeptic/Mediator roles to models.

        Returns:
            Dictionary mapping model IDs to roles.
        """
        shuffled = self.model_ids.copy()
        random.shuffle(shuffled)

        roles = [Role.ARCHITECT, Role.SKEPTIC, Role.MEDIATOR]
        assignments = {}

        for i, model_id in enumerate(shuffled[:3]):
            assignments[model_id] = roles[i]

        logger.debug(f"Role assignments: {assignments}")
        return assignments

    def _rotate_roles(self) -> None:
        """Rotate roles for the next iteration."""
        if not self._current_roles:
            return

        # Rotate: Architect -> Skeptic -> Mediator -> Architect
        rotation = {
            Role.ARCHITECT: Role.SKEPTIC,
            Role.SKEPTIC: Role.MEDIATOR,
            Role.MEDIATOR: Role.ARCHITECT,
        }

        self._current_roles = {
            model: rotation[role]
            for model, role in self._current_roles.items()
        }

        logger.debug(f"Rotated roles: {self._current_roles}")

    def _run_iteration(
        self,
        query: str,
        iteration: int,
        context: str = "",
    ) -> List[ModelResponse]:
        """Execute one round of verification.

        Args:
            query: The query being verified.
            iteration: Current iteration number.
            context: Context from previous iterations.

        Returns:
            List of model responses for this iteration.
        """
        responses = []

        # Order: Architect first, then Skeptic, then Mediator
        role_order = [Role.ARCHITECT, Role.SKEPTIC, Role.MEDIATOR]

        accumulated_context = context

        for role in role_order:
            # Find model assigned to this role
            model_id = None
            for mid, assigned_role in self._current_roles.items():
                if assigned_role == role:
                    model_id = mid
                    break

            if model_id is None:
                continue

            # Generate prompt
            prompt = RolePrompts.format_query_prompt(
                query=query,
                role=role,
                context=accumulated_context,
            )

            # Get model response
            model = self._get_model(model_id)
            try:
                content = model.generate(prompt, role.value)
            except Exception as e:
                logger.error(f"Model {model_id} failed: {e}")
                content = f"Error: {e}"

            # Check for tool calls in the response
            tool_calls = extract_tool_calls(content)
            tool_results = ""
            if tool_calls:
                logger.info(f"Model {model_id} requested {len(tool_calls)} tool(s)")
                tool_results = execute_tool_calls(tool_calls, default_registry)
                logger.debug(f"Tool results: {tool_results}")
                # Append tool results to the content
                content = f"{content}\n\n[TOOL RESULTS]\n{tool_results}"

            # Record response
            response = ModelResponse(
                model=model_id,
                role=role.value,
                content=content,
            )
            responses.append(response)

            # Record trace
            self._trace.append(TraceStep(
                iteration=iteration,
                role=role.value,
                model=model_id,
                content=content,
            ))

            # Update context for next role in this iteration
            accumulated_context += f"\n\n[{role.value.upper()}] ({model_id}):\n{content}"

        return responses

    def verify(
        self,
        query: str,
        max_iterations: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ConsensusResult:
        """Run verification protocol on a query.

        Coordinates multiple models in adversarial roles to achieve
        consensus through iterative verification rounds.

        Args:
            query: The question or claim to verify.
            max_iterations: Maximum consensus rounds (overrides config).
            context: Optional additional context for verification.

        Returns:
            ConsensusResult with consensus answer, confidence, and trace.

        Raises:
            ValueError: If query is empty.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        trace_id = generate_trace_id()
        logger.info(f"Starting verification {trace_id} for query: {query[:50]}...")

        # Initialize
        self._trace = []
        self._current_roles = self._assign_roles()

        max_iter = max_iterations or self.config["max_iterations"]
        detector = ConsensusDetector(threshold=self.config["consensus_threshold"])

        iteration_context = ""
        final_responses: List[ModelResponse] = []

        # Main verification loop
        for iteration in range(1, max_iter + 1):
            logger.info(f"Starting iteration {iteration}/{max_iter}")

            # Run iteration
            responses = self._run_iteration(
                query=query,
                iteration=iteration,
                context=iteration_context,
            )
            final_responses = responses

            # Check consensus
            consensus_reached, confidence, dissent = detector.check_consensus(responses)

            # Early stopping: if confidence is very high, accept consensus even below threshold
            if confidence >= 85.0 and iteration > 1:
                logger.info(f"High confidence ({confidence:.1f}%) reached at iteration {iteration}")
                consensus_reached = True

            if consensus_reached:
                logger.info(f"Consensus reached at iteration {iteration}")
                answer = detector.extract_consensus_answer(responses)

                return ConsensusResult(
                    consensus=answer,
                    confidence=confidence,
                    iterations=iteration,
                    trace=self._trace,
                    dissent=dissent,
                    metadata={
                        "trace_id": trace_id,
                        "query": query,
                        "models": self.model_ids,
                        "started_at": self._trace[0].timestamp if self._trace else None,
                        "completed_at": get_timestamp(),
                    },
                )

            # Prepare for next iteration
            if self.config["enable_role_rotation"]:
                self._rotate_roles()

            # Build context from this iteration
            for resp in responses:
                iteration_context += f"\n\n[{resp.role.upper()}] ({resp.model}):\n{resp.content}"

        # Max iterations reached without full consensus
        logger.warning(f"Max iterations ({max_iter}) reached without consensus")
        answer = detector.extract_consensus_answer(final_responses)
        _, confidence, dissent = detector.check_consensus(final_responses)

        return ConsensusResult(
            consensus=answer,
            confidence=confidence,
            iterations=max_iter,
            trace=self._trace,
            dissent="Max iterations reached - partial consensus",
            metadata={
                "trace_id": trace_id,
                "query": query,
                "models": self.model_ids,
                "started_at": self._trace[0].timestamp if self._trace else None,
                "completed_at": get_timestamp(),
            },
        )

    def get_trace(self) -> List[TraceStep]:
        """Get the verification trace from the last run.

        Returns:
            List of TraceStep objects.
        """
        return self._trace.copy()


class VerificationOrchestrator:
    """New verification protocol orchestrator.

    Instead of achieving consensus, this protocol:
    1. Generates an answer with a single model (proposer)
    2. Verifies the answer with multiple models (verifiers)
    3. Makes a final determination (judge)

    This approach leverages models for error detection rather than
    answer generation, which benchmarks show is more effective.
    """

    def __init__(
        self,
        models: List[str],
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize verification orchestrator.

        Args:
            models: List of model identifiers (minimum 2 required).
                   First model is proposer, rest are verifiers.
            config: Optional configuration dictionary.

        Raises:
            ValueError: If fewer than 2 models provided.
        """
        if len(models) < 2:
            raise ValueError("At least 2 models required (1 proposer + 1 verifier)")

        self.model_ids = models
        self.config = merge_configs(DEFAULT_CONFIG, config)
        self._models: Dict[str, ModelInterface] = {}
        self._trace: List[TraceStep] = []

        logger.info(f"Initialized VerificationOrchestrator with {len(models)} models")

    def _get_model(self, model_id: str) -> ModelInterface:
        """Get or create model instance."""
        if model_id not in self._models:
            self._models[model_id] = create_model(model_id)
        return self._models[model_id]

    def _generate_with_tools(
        self,
        model_id: str,
        prompt: str,
        role: Role,
    ) -> str:
        """Generate response and execute any tool calls."""
        model = self._get_model(model_id)

        try:
            content = model.generate(prompt, role.value)
        except Exception as e:
            logger.error(f"Model {model_id} failed: {e}")
            content = f"Error: {e}"

        # Check for tool calls
        tool_calls = extract_tool_calls(content)
        if tool_calls:
            logger.info(f"Model {model_id} requested {len(tool_calls)} tool(s)")
            tool_results = execute_tool_calls(tool_calls, default_registry)
            logger.debug(f"Tool results: {tool_results}")
            content = f"{content}\n\n[TOOL RESULTS]\n{tool_results}"

        return content

    def verify(
        self,
        query: str,
        initial_answer: Optional[str] = None,
    ) -> VerificationResult:
        """Run verification protocol on a query.

        Args:
            query: The question to answer or verify.
            initial_answer: Optional pre-generated answer to verify.
                          If None, proposer model generates the answer.

        Returns:
            VerificationResult with verdict, answer, and errors found.
        """
        trace_id = generate_trace_id()
        logger.info(f"Starting verification {trace_id} for query: {query[:50]}...")

        self._trace = []

        # Step 1: Get proposed answer
        if initial_answer:
            proposed_answer = initial_answer
            logger.info("Using provided initial answer")
        else:
            logger.info("Generating answer with proposer model")
            proposer_id = self.model_ids[0]
            proposer_prompt = RolePrompts.format_query_prompt(
                query=query,
                role=Role.PROPOSER,
                context="",
            )

            proposed_answer = self._generate_with_tools(
                proposer_id,
                proposer_prompt,
                Role.PROPOSER,
            )

            self._trace.append(TraceStep(
                iteration=1,
                role="proposer",
                model=proposer_id,
                content=proposed_answer,
            ))

        # Step 2: Verify with multiple verifiers
        verifier_ids = self.model_ids[1:] if initial_answer else self.model_ids[1:-1]
        verifications = []

        context = f"Original Query: {query}\n\nProposed Answer:\n{proposed_answer}"

        for i, verifier_id in enumerate(verifier_ids, 1):
            verifier_prompt = RolePrompts.format_query_prompt(
                query="Verify the correctness of the proposed answer above.",
                role=Role.VERIFIER,
                context=context,
            )

            verification = self._generate_with_tools(
                verifier_id,
                verifier_prompt,
                Role.VERIFIER,
            )

            self._trace.append(TraceStep(
                iteration=2,
                role="verifier",
                model=verifier_id,
                content=verification,
            ))

            verifications.append(verification)

        # Step 3: Judge makes final determination
        judge_id = self.model_ids[-1]
        judge_context = f"{context}\n\n"
        for i, v in enumerate(verifications, 1):
            judge_context += f"Verifier {i}:\n{v}\n\n"

        judge_prompt = RolePrompts.format_query_prompt(
            query="Make a final determination on the correctness of the proposed answer.",
            role=Role.JUDGE,
            context=judge_context,
        )

        judgment = self._generate_with_tools(
            judge_id,
            judge_prompt,
            Role.JUDGE,
        )

        self._trace.append(TraceStep(
            iteration=3,
            role="judge",
            model=judge_id,
            content=judgment,
        ))

        # Extract verdict and answer
        verdict = "UNCERTAIN"
        final_answer = proposed_answer
        errors = []

        judgment_upper = judgment.upper()
        if "VERDICT: ACCEPTED" in judgment_upper:
            verdict = "ACCEPTED"
        elif "VERDICT: REJECTED" in judgment_upper:
            verdict = "REJECTED"
            # Try to extract corrected answer
            if "FINAL_ANSWER:" in judgment:
                parts = judgment.split("FINAL_ANSWER:", 1)
                if len(parts) > 1:
                    answer_section = parts[1].split("\n")[0].strip()
                    if answer_section:
                        final_answer = answer_section

            # Extract errors
            if "ERRORS:" in judgment:
                errors_section = judgment.split("ERRORS:", 1)[1].split("\n")[0]
                if "None" not in errors_section:
                    errors.append(errors_section.strip())

        # Calculate confidence from judgment
        confidence = 50.0  # Default
        if "CONFIDENCE: HIGH" in judgment_upper:
            confidence = 85.0
        elif "CONFIDENCE: MEDIUM" in judgment_upper:
            confidence = 60.0
        elif "CONFIDENCE: LOW" in judgment_upper:
            confidence = 35.0

        logger.info(f"Verification complete: {verdict} (confidence: {confidence:.1f}%)")

        return VerificationResult(
            verdict=verdict,
            answer=final_answer,
            errors=errors,
            confidence=confidence,
            trace=self._trace,
            metadata={
                "trace_id": trace_id,
                "query": query,
                "models": self.model_ids,
                "proposer": self.model_ids[0] if not initial_answer else "external",
                "verifiers": verifier_ids,
                "judge": judge_id,
                "completed_at": get_timestamp(),
            },
        )

    def get_trace(self) -> List[TraceStep]:
        """Get the verification trace from the last run.

        Returns:
            List of TraceStep objects.
        """
        return self._trace.copy()
