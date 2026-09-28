"""Smoke tests for the command-line interface."""

import json
import time

import pytest

from maven import __version__
from maven.cli import main
from maven.models import MockModel


@pytest.fixture(autouse=True)
def no_rate_limit_pause(monkeypatch):
    """The detector waits 1s between API calls; mock models need no pause."""
    monkeypatch.setattr("maven.hallucination_detector.time.sleep", lambda seconds: None)


def test_mock_models_run_end_to_end(capsys):
    exit_code = main(["--models", "mock-a,mock-b", "--answer", "Paris.", "Capital of France?"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Risk level:" in out
    assert "Recommendation:" in out


def test_json_output(capsys):
    main(["--models", "mock-a,mock-b", "--json", "--answer", "Paris.", "Capital of France?"])

    report = json.loads(capsys.readouterr().out)
    assert report["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert report["metadata"]["models"] == ["mock-a", "mock-b"]


def test_high_risk_exit_code(monkeypatch, capsys):
    unreliable = {"reliability_check": "VERDICT: UNRELIABLE\nISSUES: invented study"}
    monkeypatch.setattr(
        "maven.hallucination_detector.create_model", lambda mid: MockModel(mid, unreliable)
    )

    exit_code = main(["--models", "mock-a,mock-b", "--answer", "A", "Q"])

    assert exit_code == 3
    assert "CRITICAL" in capsys.readouterr().out


def test_missing_api_key_is_a_clear_error(no_api_keys, capsys):
    start = time.monotonic()
    exit_code = main(["--answer", "A", "Q"])  # default models are Together AI

    assert exit_code == 1
    assert "TOGETHER_API_KEY is not set" in capsys.readouterr().err
    assert time.monotonic() - start < 2.0


def test_needs_two_models(capsys):
    assert main(["--models", "mock-a", "--answer", "A", "Q"]) == 1
    assert "At least 2 models" in capsys.readouterr().err


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out
