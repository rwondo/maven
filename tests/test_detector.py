"""Tests for the synchronous detector and the shared parsing and scoring rules."""

import time

import pytest

from maven.hallucination_detector import (
    HallucinationDetector,
    calculate_risk,
    has_reported_items,
    parse_verdict,
)
from maven.models import MockModel, ModelConfigError

R, Q, U = "RELIABLE", "QUESTIONABLE", "UNRELIABLE"
NO_FACT_ISSUES = "FACTS_VERIFIED: the date\nFACTS_FAILED: None\nCONFIDENCE: High"
FACT_ISSUES = (
    "FACTS_VERIFIED: -\nFACTS_FAILED: The 2023 Johnson study does not exist\nCONFIDENCE: High"
)
NO_CITATION_ISSUES = "CITATIONS_FOUND: none\nSUSPICIOUS: None\nCONFIDENCE: High"
CITATION_ISSUES = "CITATIONS_FOUND: Smith v. Jones\nSUSPICIOUS: Smith v. Jones looks invented"


def make_detector(monkeypatch, replies_by_model):
    """Detector whose models return scripted replies: {model_id: {role: reply}}."""
    models = {mid: MockModel(mid, responses=replies) for mid, replies in replies_by_model.items()}
    monkeypatch.setattr("maven.hallucination_detector.create_model", lambda mid: models[mid])
    return HallucinationDetector(models=list(models), rate_limit_delay=0)


def replies(verdict, fact=NO_FACT_ISSUES, citation=NO_CITATION_ISSUES):
    return {
        "reliability_check": f"VERDICT: {verdict}\nISSUES: None",
        "fact_check": fact,
        "citation_check": citation,
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("VERDICT: RELIABLE\nISSUES: None", R),
        ("**VERDICT:** UNRELIABLE", U),
        ("## Verdict: Unreliable\nISSUES: invented study", U),
        ("verdict: questionable", Q),
        ("VERDICT: [RELIABLE]", R),
        ("VERDICT: [RELIABLE / QUESTIONABLE / UNRELIABLE]", Q),  # echoed template
        ("The answer looks fine to me.", Q),  # no verdict at all
    ],
)
def test_parse_verdict(text, expected):
    assert parse_verdict(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("FACTS_FAILED: None", False),
        ("FACTS_FAILED: none identified.", False),
        ("FACTS_FAILED: N/A", False),
        ("FACTS_FAILED: [None]", False),
        ("FACTS_FAILED: Nothing found", False),
        ("FACTS_FAILED:\n- None\nCONFIDENCE: High", False),
        ("There is no labelled field here", False),
        ("**FACTS_FAILED:** The 2023 Johnson study does not exist\nCONFIDENCE: High", True),
        ("FACTS_FAILED:\n- Aspirin was first sold in 1899, not 1950\nCONFIDENCE: Low", True),
    ],
)
def test_has_reported_items(text, expected):
    assert has_reported_items(text, "FACTS_FAILED") is expected


@pytest.mark.parametrize(
    ("verdicts", "fact", "citation", "expected_risk"),
    [
        ([R, R, R], NO_FACT_ISSUES, NO_CITATION_ISSUES, "LOW"),
        ([R, R, R, Q], NO_FACT_ISSUES, NO_CITATION_ISSUES, "LOW"),  # exactly 75% reliable
        ([R, R, Q], NO_FACT_ISSUES, NO_CITATION_ISSUES, "MEDIUM"),
        ([R, U, R], NO_FACT_ISSUES, NO_CITATION_ISSUES, "HIGH"),
        ([R, R, R], FACT_ISSUES, NO_CITATION_ISSUES, "HIGH"),
        ([R, R, R], NO_FACT_ISSUES, CITATION_ISSUES, "HIGH"),
        ([U, U, R], NO_FACT_ISSUES, NO_CITATION_ISSUES, "CRITICAL"),
        ([R, R, R], FACT_ISSUES, CITATION_ISSUES, "CRITICAL"),
        ([R, U, R], NO_FACT_ISSUES, CITATION_ISSUES, "CRITICAL"),
    ],
)
def test_calculate_risk_rules(verdicts, fact, citation, expected_risk):
    risk, _, _, _ = calculate_risk(verdicts, fact, citation)
    assert risk == expected_risk


def test_calculate_risk_scores_and_disagreements():
    risk, share, flags, disagreements = calculate_risk([R, R, U], FACT_ISSUES, NO_CITATION_ISSUES)
    assert share == pytest.approx(66.67, abs=0.01)
    assert flags == [
        "1/3 models rated the answer UNRELIABLE",
        "Fact check found wrong or unverifiable claims",
    ]
    assert disagreements == ["Models disagree on reliability: RELIABLE, RELIABLE, UNRELIABLE"]
    assert risk == "CRITICAL"


def test_requires_two_models():
    with pytest.raises(ValueError, match="At least 2 models"):
        HallucinationDetector(models=["mock-a"])


def test_detect_all_reliable_is_low(monkeypatch):
    detector = make_detector(monkeypatch, {"m1": replies(R), "m2": replies(R), "m3": replies(R)})
    report = detector.detect("Who wrote Hamlet?", "William Shakespeare.")

    assert report.risk_level == "LOW"
    assert report.verdicts == [R, R, R]
    assert report.reliable_share == 100
    assert report.flags == []
    assert report.metadata["models"] == ["m1", "m2", "m3"]


def test_detect_trace_has_one_step_per_call(monkeypatch):
    detector = make_detector(monkeypatch, {"m1": replies(R), "m2": replies(Q), "m3": replies(R)})
    report = detector.detect("Q", "A")

    assert [(s.role, s.model) for s in report.trace] == [
        ("reliability_check", "m1"),
        ("reliability_check", "m2"),
        ("reliability_check", "m3"),
        ("fact_check", "m1"),
        ("citation_check", "m2"),
    ]
    assert report.risk_level == "MEDIUM"


def test_detect_flags_fabricated_citation(monkeypatch):
    detector = make_detector(
        monkeypatch,
        {"m1": replies(R), "m2": replies(R, citation=CITATION_ISSUES)},
    )
    report = detector.detect("Cite a case", "See Smith v. Jones (2031).")

    assert report.risk_level == "HIGH"
    assert "Citation check found suspicious or unsourced references" in report.flags


def test_detect_batch_keeps_order_and_reports_progress(monkeypatch):
    detector = make_detector(monkeypatch, {"m1": replies(R), "m2": replies(R)})
    progress = []
    items = [{"query": f"Q{i}", "answer": f"A{i}"} for i in range(3)]

    reports = detector.detect_batch(items, progress_callback=lambda d, t: progress.append((d, t)))

    assert [r.metadata["query"] for r in reports] == ["Q0", "Q1", "Q2"]
    assert progress == [(1, 3), (2, 3), (3, 3)]


def test_is_hallucination_threshold(monkeypatch):
    detector = make_detector(monkeypatch, {"m1": replies(R), "m2": replies(Q)})  # MEDIUM

    assert detector.is_hallucination("Q", "A") is True
    assert detector.is_hallucination("Q", "A", threshold=["HIGH", "CRITICAL"]) is False


class FailingModel(MockModel):
    def generate(self, prompt: str, role: str) -> str:
        raise TimeoutError("provider timed out")


def test_failed_call_is_flagged_not_silent(monkeypatch):
    models = {"m1": MockModel("m1", replies(R)), "m2": FailingModel("m2")}
    monkeypatch.setattr("maven.hallucination_detector.create_model", lambda mid: models[mid])
    detector = HallucinationDetector(models=["m1", "m2"], rate_limit_delay=0)

    report = detector.detect("Q", "A")

    assert "2/4 model calls failed, so the check is incomplete" in report.flags
    assert report.risk_level in {"HIGH", "CRITICAL"}
    assert [s.error for s in report.trace if s.model == "m2"] == ["provider timed out"] * 2


def test_missing_api_key_raises_immediately(no_api_keys):
    detector = HallucinationDetector(models=["together/llama-3.1-8b", "together/qwen-2.5-7b"])

    start = time.monotonic()
    with pytest.raises(ModelConfigError, match="TOGETHER_API_KEY is not set"):
        detector.detect("Q", "A")
    assert time.monotonic() - start < 1.0


def test_batch_stops_on_setup_errors(no_api_keys):
    detector = HallucinationDetector(models=["together/llama-3.1-8b", "together/qwen-2.5-7b"])

    with pytest.raises(ModelConfigError):
        detector.detect_batch([{"query": "Q", "answer": "A"}] * 3)
