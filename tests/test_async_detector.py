"""Tests for the async detector: same scoring, concurrent calls."""

import asyncio
import re

import pytest

from maven.async_hallucination_detector import AsyncHallucinationDetector
from maven.async_models import AsyncModelInterface
from maven.hallucination_detector import HallucinationReport

ROLE_DELAYS = {"reliability_check": 0.03, "fact_check": 0.0, "citation_check": 0.01}


class EchoModel(AsyncModelInterface):
    """Votes RELIABLE and echoes the question back, so each reply shows which check it served.

    Calls finish in a different order from the one they were started in, and the
    class records how many calls were in flight at the same time.
    """

    in_flight = 0
    peak = 0

    def __init__(self, model_id: str, verdict: str = "RELIABLE"):
        super().__init__(model_id)
        self.verdict = verdict

    async def generate(self, prompt: str, role: str) -> str:
        EchoModel.in_flight += 1
        EchoModel.peak = max(EchoModel.peak, EchoModel.in_flight)
        try:
            await asyncio.sleep(ROLE_DELAYS[role])
            question = re.search(r"Original Question: (.*)", prompt).group(1)
            return f"VERDICT: {self.verdict}\nFACTS_FAILED: None\nSUSPICIOUS: None\nQ={question}"
        finally:
            EchoModel.in_flight -= 1


@pytest.fixture
def echo_models(monkeypatch):
    EchoModel.in_flight = EchoModel.peak = 0
    models: dict[str, EchoModel] = {}

    def factory(model_id: str) -> EchoModel:
        verdict = "UNRELIABLE" if model_id.startswith("bad") else "RELIABLE"
        return models.setdefault(model_id, EchoModel(model_id, verdict))

    monkeypatch.setattr("maven.async_hallucination_detector.create_async_model", factory)
    return models


def test_requires_two_models():
    with pytest.raises(ValueError, match="At least 2 models"):
        AsyncHallucinationDetector(models=["m1"])


async def test_detect_all_reliable_is_low(echo_models):
    detector = AsyncHallucinationDetector(models=["m1", "m2", "m3"], rate_limit_delay=0)
    report = await detector.detect("Who wrote Hamlet?", "Shakespeare.")

    assert isinstance(report, HallucinationReport)
    assert report.risk_level == "LOW"
    assert report.verdicts == ["RELIABLE"] * 3
    assert report.metadata["run_async"] is True


async def test_unreliable_votes_raise_risk(echo_models):
    detector = AsyncHallucinationDetector(models=["bad1", "bad2", "m3"], rate_limit_delay=0)
    report = await detector.detect("Q", "A")

    assert report.risk_level == "CRITICAL"


async def test_trace_order_is_fixed_even_when_calls_finish_out_of_order(echo_models):
    detector = AsyncHallucinationDetector(models=["m1", "m2", "m3"], rate_limit_delay=0)
    report = await detector.detect("Q", "A")

    assert [(s.role, s.model) for s in report.trace] == [
        ("reliability_check", "m1"),
        ("reliability_check", "m2"),
        ("reliability_check", "m3"),
        ("fact_check", "m1"),
        ("citation_check", "m2"),
    ]


async def test_batch_keeps_order_and_does_not_mix_traces(echo_models):
    detector = AsyncHallucinationDetector(
        models=["m1", "m2"], rate_limit_delay=0, max_concurrent_calls=8
    )
    items = [{"query": f"question-{i}", "answer": "A"} for i in range(6)]

    reports = await detector.detect_batch(items, max_concurrent=6)

    assert [r.metadata["query"] for r in reports] == [f"question-{i}" for i in range(6)]
    for i, report in enumerate(reports):
        assert len(report.trace) == 4
        assert all(step.content.endswith(f"Q=question-{i}") for step in report.trace)


async def test_concurrent_calls_are_capped(echo_models):
    detector = AsyncHallucinationDetector(
        models=["m1", "m2", "m3"], rate_limit_delay=0, max_concurrent_calls=2
    )
    await detector.detect_batch([{"query": f"q{i}", "answer": "a"} for i in range(4)])

    assert EchoModel.peak == 2


async def test_batch_progress_callback(echo_models):
    detector = AsyncHallucinationDetector(models=["m1", "m2"], rate_limit_delay=0)
    progress = []

    await detector.detect_batch(
        [{"query": "Q", "answer": "A"}] * 3, progress_callback=lambda d, t: progress.append((d, t))
    )

    assert sorted(progress) == [(1, 3), (2, 3), (3, 3)]


async def test_batch_continues_after_an_item_fails(echo_models, monkeypatch):
    detector = AsyncHallucinationDetector(models=["m1", "m2"], rate_limit_delay=0)
    real_detect = detector.detect

    async def flaky_detect(query, answer):
        if query == "boom":
            raise RuntimeError("provider outage")
        return await real_detect(query, answer)

    monkeypatch.setattr(detector, "detect", flaky_detect)
    reports = await detector.detect_batch(
        [{"query": "ok", "answer": "A"}, {"query": "boom", "answer": "A"}]
    )

    assert reports[0].risk_level == "LOW"
    assert reports[1].risk_level == "HIGH"
    assert reports[1].flags == ["Detection error: provider outage"]


async def test_is_hallucination(echo_models):
    detector = AsyncHallucinationDetector(models=["bad1", "m2"], rate_limit_delay=0)
    assert await detector.is_hallucination("Q", "A") is True


def test_detector_can_be_reused_across_event_loops(echo_models):
    detector = AsyncHallucinationDetector(models=["m1", "m2"], rate_limit_delay=0)

    first = asyncio.run(detector.detect("Q", "A"))
    second = asyncio.run(detector.detect("Q", "A"))

    assert first.risk_level == second.risk_level == "LOW"
