"""
Async orchestration for parallel model calls.

This module provides an asynchronous version of the ConsensusOrchestrator
that can run model calls in parallel for improved performance.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from maven.consensus import (
    ConsensusDetector,
    ConsensusResult,
    ModelResponse,
    TraceStep,
)
from maven.models import ModelInterface
from maven.async_models import create_async_model, AsyncModelInterface
from maven.roles import Role, RolePrompts
from maven.utils import (
    DEFAULT_CONFIG,
    generate_trace_id,
    get_timestamp,
    merge_configs,
    validate_models,
)

logger = logging.getLogger(__name__)


class AsyncConsensusOrchestrator:
    """Asynchronous orchestrator for parallel multi-model verification.

    This class provides the same functionality as ConsensusOrchestrator
    but uses async/await for parallel model calls within each iteration.

    Example:
        >>> orchestrator = AsyncConsensusOrchestrator(
        ...     models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
        ... )
        >>> result = await orchestrator.verify("What is the capital of France?")
        >>> print(result.consensus)
        Paris
    """

    def __init__(
        self,
        models: List[str],
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize async orchestrator.

        Args:
            models: List of model identifiers (minimum 3 required).
            config: Optional configuration dictionary.
        """
        validate_models(models)

        self.model_ids = models
        self.config = merge_configs(DEFAULT_CONFIG, config)
        self._models: Dict[str, AsyncModelInterface] = {}
        self._trace: List[TraceStep] = []
        self._current_roles: Dict[str, Role] = {}

        logger.info(f"Initialized AsyncConsensusOrchestrator with {len(models)} models")

    def _get_model(self, model_id: str) -> AsyncModelInterface:
        """Get or create async model instance."""
        if model_id not in self._models:
            self._models[model_id] = create_async_model(model_id)
        return self._models[model_id]

    def _assign_roles(self) -> Dict[str, Role]:
        """Randomly assign roles to models."""
        import random
        shuffled = self.model_ids.copy()
        random.shuffle(shuffled)

        roles = [Role.ARCHITECT, Role.SKEPTIC, Role.MEDIATOR]
        return {shuffled[i]: roles[i] for i in range(3)}

    def _rotate_roles(self) -> None:
        """Rotate roles for next iteration."""
        if not self._current_roles:
            return

        rotation = {
            Role.ARCHITECT: Role.SKEPTIC,
            Role.SKEPTIC: Role.MEDIATOR,
            Role.MEDIATOR: Role.ARCHITECT,
        }
        self._current_roles = {
            model: rotation[role]
            for model, role in self._current_roles.items()
        }

    async def _generate_response(
        self,
        model_id: str,
        role: Role,
        prompt: str,
    ) -> ModelResponse:
        """Generate a single model response asynchronously."""
        model = self._get_model(model_id)
        try:
            content = await model.generate(prompt, role.value)
        except Exception as e:
            logger.error(f"Model {model_id} failed: {e}")
            content = f"Error: {e}"

        return ModelResponse(
            model=model_id,
            role=role.value,
            content=content,
        )

    async def _run_iteration_parallel(
        self,
        query: str,
        iteration: int,
        context: str = "",
    ) -> List[ModelResponse]:
        """Run iteration with parallel initial calls where possible.

        Note: Full parallelization isn't possible because Skeptic needs
        Architect's response and Mediator needs both. However, we can
        optimize by preparing prompts in advance.
        """
        responses = []
        accumulated_context = context

        # Sequential execution required due to role dependencies
        for role in [Role.ARCHITECT, Role.SKEPTIC, Role.MEDIATOR]:
            model_id = None
            for mid, assigned_role in self._current_roles.items():
                if assigned_role == role:
                    model_id = mid
                    break

            if model_id is None:
                continue

            prompt = RolePrompts.format_query_prompt(
                query=query,
                role=role,
                context=accumulated_context,
            )

            response = await self._generate_response(model_id, role, prompt)
            responses.append(response)

            self._trace.append(TraceStep(
                iteration=iteration,
                role=role.value,
                model=model_id,
                content=response.content,
            ))

            accumulated_context += f"\n\n[{role.value.upper()}] ({model_id}):\n{response.content}"

        return responses

    async def verify(
        self,
        query: str,
        max_iterations: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ConsensusResult:
        """Run async verification protocol.

        Args:
            query: The question or claim to verify.
            max_iterations: Maximum consensus rounds.
            context: Optional additional context.

        Returns:
            ConsensusResult with consensus, confidence, and trace.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        trace_id = generate_trace_id()
        logger.info(f"Starting async verification {trace_id}")

        self._trace = []
        self._current_roles = self._assign_roles()

        max_iter = max_iterations or self.config["max_iterations"]
        detector = ConsensusDetector(threshold=self.config["consensus_threshold"])

        iteration_context = ""
        final_responses: List[ModelResponse] = []

        for iteration in range(1, max_iter + 1):
            logger.info(f"Async iteration {iteration}/{max_iter}")

            responses = await self._run_iteration_parallel(
                query=query,
                iteration=iteration,
                context=iteration_context,
            )
            final_responses = responses

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
                        "async": True,
                        "completed_at": get_timestamp(),
                    },
                )

            if self.config["enable_role_rotation"]:
                self._rotate_roles()

            for resp in responses:
                iteration_context += f"\n\n[{resp.role.upper()}] ({resp.model}):\n{resp.content}"

        logger.warning(f"Max iterations ({max_iter}) reached")
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
                "async": True,
                "completed_at": get_timestamp(),
            },
        )

    async def verify_batch(
        self,
        queries: List[str],
        max_iterations: Optional[int] = None,
        max_concurrent: int = 3,
    ) -> List[ConsensusResult]:
        """Verify multiple queries with controlled concurrency.

        Args:
            queries: List of queries to verify.
            max_iterations: Maximum iterations per query.
            max_concurrent: Maximum concurrent verifications.

        Returns:
            List of ConsensusResult objects.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def verify_with_limit(query: str) -> ConsensusResult:
            async with semaphore:
                return await self.verify(query, max_iterations)

        tasks = [verify_with_limit(q) for q in queries]
        return await asyncio.gather(*tasks)
