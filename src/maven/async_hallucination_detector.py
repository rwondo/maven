"""Async version of the detector: sends the model calls for a check concurrently.

It uses the same prompts, parsing and scoring as HallucinationDetector. The
only difference is that calls run at the same time (asyncio.gather) instead of
one after another, with a semaphore capping how many are in flight at once.
"""

import asyncio
import logging
from collections.abc import Callable

from maven.async_models import AsyncModelInterface, create_async_model
from maven.hallucination_detector import (
    CITATION_PROMPT,
    DEFAULT_THRESHOLD,
    FACT_CHECK_PROMPT,
    RELIABILITY_PROMPT,
    HallucinationReport,
    TraceStep,
    build_report,
    error_report,
)
from maven.models import ModelConfigError

logger = logging.getLogger(__name__)


class AsyncHallucinationDetector:
    """Checks answers with concurrent model calls.

    Example:
        detector = AsyncHallucinationDetector(
            models=["together/llama-3.1-8b", "together/qwen-2.5-7b", "together/mixtral-8x7b"]
        )
        report = await detector.detect(query="...", answer="...")
        reports = await detector.detect_batch(
            [{"query": "Q1", "answer": "A1"}, {"query": "Q2", "answer": "A2"}],
            max_concurrent=3,
        )
    """

    def __init__(
        self,
        models: list[str],
        rate_limit_delay: float = 0.5,
        max_concurrent_calls: int | None = None,
    ):
        """Create a detector.

        Args:
            models: Reviewer model identifiers (at least 2). The first also runs the
                fact check and the second the citation check.
            rate_limit_delay: Seconds each call waits before it is sent.
            max_concurrent_calls: Cap on API calls in flight at once, across all
                checks (default: the number of models).
        """
        if len(models) < 2:
            raise ValueError("At least 2 models required for hallucination detection")

        self.model_ids = models
        self._models: dict[str, AsyncModelInterface] = {}
        self._rate_limit_delay = rate_limit_delay
        self._max_concurrent_calls = max_concurrent_calls or len(models)
        # A semaphore belongs to one event loop, so it is created on first use per loop.
        self._call_limiter: asyncio.Semaphore | None = None
        self._limiter_loop: asyncio.AbstractEventLoop | None = None

    def _get_model(self, model_id: str) -> AsyncModelInterface:
        if model_id not in self._models:
            self._models[model_id] = create_async_model(model_id)
        return self._models[model_id]

    def _limiter(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        if self._call_limiter is None or self._limiter_loop is not loop:
            self._call_limiter = asyncio.Semaphore(self._max_concurrent_calls)
            self._limiter_loop = loop
        return self._call_limiter

    async def _call(self, model_id: str, prompt: str, role: str) -> TraceStep:
        """Run one model call. API errors are recorded on the step; setup errors raise."""
        async with self._limiter():
            await asyncio.sleep(self._rate_limit_delay)
            try:
                content = await self._get_model(model_id).generate(prompt, role)
            except ModelConfigError:
                raise
            except Exception as e:
                logger.error(f"Model {model_id} failed: {e}")
                return TraceStep(role=role, model=model_id, content=f"Error: {e}", error=str(e))
        return TraceStep(role=role, model=model_id, content=content)

    async def detect(self, query: str, answer: str) -> HallucinationReport:
        """Check one answer. Sends len(models) + 2 API calls concurrently."""
        fields = {"query": query, "answer": answer}
        reliability_prompt = RELIABILITY_PROMPT.format(**fields)
        *reliability_steps, fact_step, citation_step = await asyncio.gather(
            *(self._call(m, reliability_prompt, "reliability_check") for m in self.model_ids),
            self._call(self.model_ids[0], FACT_CHECK_PROMPT.format(**fields), "fact_check"),
            self._call(self.model_ids[1], CITATION_PROMPT.format(**fields), "citation_check"),
        )
        return build_report(
            query, answer, list(reliability_steps), fact_step, citation_step, run_async=True
        )

    async def detect_batch(
        self,
        items: list[dict[str, str]],
        max_concurrent: int = 5,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[HallucinationReport]:
        """Check several {"query": ..., "answer": ...} items; results keep input order.

        Args:
            items: The question/answer pairs to check.
            max_concurrent: How many items are checked at the same time.
            progress_callback: Called as callback(done, total) after each item.
        """
        item_limiter = asyncio.Semaphore(max_concurrent)
        completed = 0

        async def run(index: int, item: dict[str, str]) -> HallucinationReport:
            nonlocal completed
            query = item.get("query", "")
            async with item_limiter:
                try:
                    report = await self.detect(query, item.get("answer", ""))
                except ModelConfigError:
                    raise
                except Exception as e:
                    logger.error(f"Error detecting item {index + 1}: {e}")
                    report = error_report(query, e)
            completed += 1
            if progress_callback:
                progress_callback(completed, len(items))
            return report

        return list(await asyncio.gather(*(run(i, item) for i, item in enumerate(items))))

    async def is_hallucination(
        self, query: str, answer: str, threshold: list[str] | None = None
    ) -> bool:
        """True if the risk level is in `threshold` (default: MEDIUM, HIGH, CRITICAL)."""
        levels = threshold if threshold is not None else DEFAULT_THRESHOLD
        report = await self.detect(query, answer)
        return report.risk_level in levels
