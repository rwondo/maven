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
)
from maven.models import ModelInterface, create_model
from maven.roles import Role, RolePrompts
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
