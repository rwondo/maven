"""
Async Hallucination Detection for MAVEN.

Provides asynchronous hallucination detection with parallel processing
for improved performance on batch operations.
"""

import asyncio
import logging
from typing import Any, Callable, Optional

from maven.async_models import AsyncModelInterface, create_async_model
from maven.consensus import TraceStep
from maven.hallucination_detector import (
    HallucinationReport,
)
from maven.mcp_integration import MCPServerRegistry, create_mcp_server
from maven.utils import DEFAULT_CONFIG, generate_trace_id, get_timestamp, merge_configs

logger = logging.getLogger(__name__)


class AsyncHallucinationDetector:
    """Asynchronous multi-model hallucination detection system.

    Uses multiple models to verify responses and flag potential hallucinations,
    with full async/await support for parallel processing.

    Features:
        - Parallel model calls for faster detection
        - Batch detection with concurrency control
        - Domain-specific verification (medical, legal, financial)
        - MCP tool integration
        - Rate limiting

    Example:
        detector = AsyncHallucinationDetector(
            models=["together/llama-3.1-8b", "together/qwen-2.5-7b", "together/mixtral-8x7b"]
        )

        # Single detection
        report = await detector.detect(
            query="What is aspirin?",
            answer="Aspirin is...",
            domain="medical"
        )

        # Batch detection with parallelism
        reports = await detector.detect_batch([
            {"query": "Q1", "answer": "A1"},
            {"query": "Q2", "answer": "A2"},
        ], max_concurrent=3)
    """

    def __init__(
        self,
        models: list[str],
        config: Optional[dict[str, Any]] = None,
        mcp_servers: Optional[list[dict[str, Any]]] = None,
        rate_limit_delay: float = 0.5,
    ):
        """Initialize async hallucination detector.

        Args:
            models: List of model identifiers (minimum 2 required).
            config: Optional configuration dictionary.
            mcp_servers: Optional list of MCP server configurations.
            rate_limit_delay: Delay in seconds between API calls (default: 0.5).
        """
        if len(models) < 2:
            raise ValueError("At least 2 models required for hallucination detection")

        self.model_ids = models
        self.config = merge_configs(DEFAULT_CONFIG, config)
        self._models: dict[str, AsyncModelInterface] = {}
        self._trace: list[TraceStep] = []
        self._rate_limit_delay = rate_limit_delay
        self._rate_limiter = asyncio.Semaphore(len(models))  # Limit concurrent calls

        # Initialize MCP server registry
        self.mcp_registry = MCPServerRegistry()
        if mcp_servers:
            for server_config in mcp_servers:
                server_type = server_config.get("type", "stdio")
                server_name = server_config.get("name", f"server_{len(self.mcp_registry.servers)}")
                server = create_mcp_server(server_type, server_name, server_config)
                if server:
                    self.mcp_registry.register_server(server)

        logger.info(f"Initialized AsyncHallucinationDetector with {len(models)} models")

    def _get_model(self, model_id: str) -> AsyncModelInterface:
        """Get or create async model instance."""
        if model_id not in self._models:
            self._models[model_id] = create_async_model(model_id)
        return self._models[model_id]

    async def _generate_with_rate_limit(
        self,
        model_id: str,
        prompt: str,
        role: str,
    ) -> str:
        """Generate response with rate limiting."""
        async with self._rate_limiter:
            await asyncio.sleep(self._rate_limit_delay)
            model = self._get_model(model_id)
            try:
                content = await model.generate(prompt, role)
            except Exception as e:
                logger.error(f"Model {model_id} failed: {e}")
                content = f"Error: {e}"
            return content

    async def _run_consistency_checks(
        self,
        query: str,
        answer: str,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Run consistency checks across all models in parallel."""
        CONSISTENCY_PROMPT = f"""You are verifying an AI-generated answer for potential hallucinations.

CRITICAL: This is for a high-stakes domain. Flag ANY suspicious claims.

Original Question: {query}

Answer to Verify:
{answer}

Your task: Check if this answer is consistent and factually sound.

Look for:
- Fabricated facts or citations
- Logical inconsistencies
- Unsupported claims
- Vague or hedging language that might hide uncertainty

Respond with:
VERDICT: [RELIABLE / QUESTIONABLE / UNRELIABLE]
ISSUES: [List specific problems, or "None" if answer seems sound]
CONFIDENCE: [High/Medium/Low in your assessment]"""

        # Run all consistency checks in parallel
        tasks = [
            self._generate_with_rate_limit(model_id, CONSISTENCY_PROMPT, f"consistency_checker_{i}")
            for i, model_id in enumerate(self.model_ids)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        model_responses = []
        consistency_checks = []

        for _i, (model_id, response) in enumerate(zip(self.model_ids, responses)):
            if isinstance(response, Exception):
                response = f"Error: {response}"

            model_responses.append(response)

            # Parse verdict
            verdict = "QUESTIONABLE"
            if "VERDICT: RELIABLE" in str(response).upper():
                verdict = "RELIABLE"
            elif "VERDICT: UNRELIABLE" in str(response).upper():
                verdict = "UNRELIABLE"

            consistency_checks.append(
                {"model": model_id, "verdict": verdict, "response": str(response)[:300]}
            )

            self._trace.append(
                TraceStep(
                    iteration=1,
                    role="consistency_checker",
                    model=model_id,
                    content=str(response),
                )
            )

        return model_responses, consistency_checks

    async def _run_fact_check(self, query: str, answer: str) -> dict[str, Any]:
        """Run fact check using first model."""
        FACT_CHECK_PROMPT = f"""You are fact-checking an AI answer for a critical application.

Original Question: {query}

Answer to Check:
{answer}

Your task: Verify specific factual claims in this answer.

Report:
FACTS_VERIFIED: [List what you checked]
FACTS_FAILED: [List any facts that couldn't be verified or were wrong]
CONFIDENCE: [High/Medium/Low]"""

        response = await self._generate_with_rate_limit(
            self.model_ids[0], FACT_CHECK_PROMPT, "fact_checker"
        )

        self._trace.append(
            TraceStep(
                iteration=2,
                role="fact_checker",
                model=self.model_ids[0],
                content=response,
            )
        )

        return {
            "model": self.model_ids[0],
            "response": response[:500],
        }

    async def _run_citation_check(self, query: str, answer: str) -> dict[str, Any]:
        """Run citation check using second model."""
        CITATION_PROMPT = f"""You are checking an answer for fabricated or misleading citations/sources.

Original Question: {query}

Answer to Check:
{answer}

Look for:
- Citations or references that seem fabricated
- Vague references ("studies show", "experts say")
- Specific claims without sources
- Real-sounding but potentially fake case names/statutes

Report:
CITATIONS_FOUND: [List any citations/references mentioned]
SUSPICIOUS: [Flag any that seem fabricated or unsourced]
CONFIDENCE: [High/Medium/Low]"""

        model_id = self.model_ids[1] if len(self.model_ids) > 1 else self.model_ids[0]
        response = await self._generate_with_rate_limit(
            model_id, CITATION_PROMPT, "citation_checker"
        )

        self._trace.append(
            TraceStep(
                iteration=3,
                role="citation_checker",
                model=model_id,
                content=response,
            )
        )

        return {
            "model": model_id,
            "response": response[:500],
        }

    def _calculate_risk(
        self,
        consistency_checks: list[dict[str, Any]],
        fact_response: str,
        citation_response: str,
    ) -> tuple[str, float, list[str], list[str]]:
        """Calculate risk level and confidence score."""
        flags = []
        disagreements = []

        # Check consistency across models
        verdicts = [c["verdict"] for c in consistency_checks]
        reliable_count = verdicts.count("RELIABLE")
        unreliable_count = verdicts.count("UNRELIABLE")

        if unreliable_count > 0:
            flags.append(f"{unreliable_count}/{len(verdicts)} models flagged as UNRELIABLE")

        if len(set(verdicts)) > 1:
            disagreements.append(f"Models disagree on reliability: {verdicts}")

        # Check fact verification
        if (
            "FACTS_FAILED" in fact_response
            and "None" not in fact_response.split("FACTS_FAILED")[1][:100]
        ):
            flags.append("Fact verification failed for some claims")

        # Check citations
        if (
            "SUSPICIOUS" in citation_response
            and "None" not in citation_response.split("SUSPICIOUS")[1][:100]
        ):
            flags.append("Suspicious or unsourced citations detected")

        # Calculate scores
        consistency_score = (reliable_count / len(verdicts)) * 100
        confidence_score = consistency_score

        # Determine risk level
        if unreliable_count >= 2 or len(flags) >= 2:
            risk_level = "CRITICAL"
        elif unreliable_count > 0 or len(flags) > 0:
            risk_level = "HIGH"
        elif confidence_score < 75:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return risk_level, confidence_score, flags, disagreements

    async def detect(
        self,
        query: str,
        answer: str,
        domain: Optional[str] = None,
    ) -> HallucinationReport:
        """Detect potential hallucinations asynchronously.

        Args:
            query: The original question/query.
            answer: The answer to verify.
            domain: Optional domain context (e.g., "medical", "legal").

        Returns:
            HallucinationReport with risk assessment.
        """
        trace_id = generate_trace_id()
        logger.info(f"Starting async hallucination detection {trace_id}")

        self._trace = []

        # Run all checks in parallel where possible
        consistency_task = self._run_consistency_checks(query, answer)
        fact_task = self._run_fact_check(query, answer)
        citation_task = self._run_citation_check(query, answer)

        # Gather results
        (model_responses, consistency_checks), fact_check, citation_check = await asyncio.gather(
            consistency_task, fact_task, citation_task
        )

        # Calculate risk
        risk_level, confidence_score, flags, disagreements = self._calculate_risk(
            consistency_checks,
            fact_check["response"],
            citation_check["response"],
        )

        consistency_score = (
            len([c for c in consistency_checks if c["verdict"] == "RELIABLE"])
            / len(consistency_checks)
        ) * 100

        logger.info(
            f"Async detection complete: {risk_level} risk ({confidence_score:.1f}% confidence)"
        )

        return HallucinationReport(
            risk_level=risk_level,
            confidence_score=confidence_score,
            flags=flags,
            consistency_score=consistency_score,
            fact_checks=[fact_check],
            citation_checks=[citation_check],
            logic_checks=[],
            model_responses=model_responses,
            disagreements=disagreements,
            trace=self._trace,
            metadata={
                "trace_id": trace_id,
                "query": query,
                "answer": answer[:500],
                "domain": domain,
                "models": self.model_ids,
                "async": True,
                "completed_at": get_timestamp(),
            },
        )

    async def detect_batch(
        self,
        items: list[dict[str, str]],
        domain: Optional[str] = None,
        max_concurrent: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> list[HallucinationReport]:
        """Detect hallucinations in a batch with controlled concurrency.

        Args:
            items: List of dicts with 'query' and 'answer' keys.
            domain: Optional domain context for all items.
            max_concurrent: Maximum concurrent detections (default: 5).
            progress_callback: Optional callback(current, total) for progress.

        Returns:
            List of HallucinationReport for each item.

        Example:
            reports = await detector.detect_batch([
                {"query": "Q1", "answer": "A1"},
                {"query": "Q2", "answer": "A2"},
            ], max_concurrent=3)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results: list[Optional[HallucinationReport]] = [None] * len(items)
        completed = 0

        async def detect_with_limit(index: int, item: dict[str, str]) -> None:
            nonlocal completed
            async with semaphore:
                query = item.get("query", "")
                answer = item.get("answer", "")
                item_domain = item.get("domain", domain)

                try:
                    report = await self.detect(query, answer, item_domain)
                    results[index] = report
                except Exception as e:
                    logger.error(f"Error detecting item {index + 1}: {e}")
                    results[index] = HallucinationReport(
                        risk_level="HIGH",
                        confidence_score=0.0,
                        flags=[f"Detection error: {str(e)}"],
                        consistency_score=0.0,
                        fact_checks=[],
                        citation_checks=[],
                        logic_checks=[],
                        model_responses=[],
                        disagreements=[],
                        trace=[],
                        metadata={"error": str(e), "query": query},
                    )

                completed += 1
                if progress_callback:
                    progress_callback(completed, len(items))

        # Create all tasks
        tasks = [detect_with_limit(i, item) for i, item in enumerate(items)]

        # Run all with concurrency control
        await asyncio.gather(*tasks)

        return results

    async def is_hallucination(
        self,
        query: str,
        answer: str,
        domain: Optional[str] = None,
        threshold: Optional[list[str]] = None,
    ) -> bool:
        """Quick async check if an answer is likely a hallucination.

        Args:
            query: The original question.
            answer: The answer to check.
            domain: Optional domain context.
            threshold: Risk levels to flag as hallucinations.

        Returns:
            True if likely a hallucination, False otherwise.
        """
        if threshold is None:
            threshold = ["CRITICAL", "HIGH", "MEDIUM"]

        report = await self.detect(query, answer, domain)
        return report.risk_level in threshold

    def get_trace(self) -> list[TraceStep]:
        """Get detection trace from last run."""
        return self._trace.copy()
