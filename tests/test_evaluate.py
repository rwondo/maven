"""Tests for scripts/evaluate_truthfulqa.py (no network: the dataset download is faked)."""

import json

import evaluate_truthfulqa as ev
import pytest

ROWS = [
    {
        "Question": f"Question {i}?",
        "Best Answer": f"Right {i}",
        "Best Incorrect Answer": f"Wrong {i}",
        "Category": "Misconceptions",
    }
    for i in range(10)
] + [
    {
        "Question": "No wrong answer?",
        "Best Answer": "x",
        "Best Incorrect Answer": " ",
        "Category": "c",
    }
]


def test_build_items_is_balanced_and_reproducible():
    items = ev.build_items(ROWS, n=4, seed=1)

    assert len(items) == 8
    assert sum(item.is_hallucination for item in items) == 4
    assert items == ev.build_items(ROWS, n=4, seed=1)
    assert all(item.question != "No wrong answer?" for item in items)  # incomplete rows skipped


def test_build_items_rejects_too_large_n():
    with pytest.raises(ValueError, match="usable questions"):
        ev.build_items(ROWS, n=11, seed=0)


@pytest.mark.parametrize(
    ("successes", "total", "expected"),
    [
        (50, 100, (0.404, 0.596)),
        (0, 10, (0.0, 0.278)),
        (10, 10, (0.722, 1.0)),
    ],
)
def test_wilson_interval(successes, total, expected):
    low, high = ev.wilson_interval(successes, total)
    assert low == pytest.approx(expected[0], abs=0.001)
    assert high == pytest.approx(expected[1], abs=0.001)


def test_score_counts_catches_and_false_alarms():
    labels = [True, True, True, False, False]  # True = wrong answer
    flagged = [True, True, False, True, False]

    m = ev.score(labels, flagged)

    assert (m.caught, m.wrong_answers, m.false_alarms, m.correct_answers) == (2, 3, 1, 2)
    assert m.catch_rate == pytest.approx(2 / 3)
    assert m.false_alarm_rate == pytest.approx(1 / 2)
    assert m.accuracy == pytest.approx(3 / 5)


def test_flag_everything_baseline_is_50_percent_accurate_on_balanced_data():
    m = ev.score([True, False] * 5, [True] * 10)
    assert (m.catch_rate, m.false_alarm_rate, m.accuracy) == (1.0, 1.0, 0.5)


def test_end_to_end_with_mock_models(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ev, "load_rows", lambda: ROWS)
    output = tmp_path / "results.json"

    exit_code = ev.main(
        [
            "--n",
            "3",
            "--models",
            "mock-a,mock-b",
            "--rate-limit-delay",
            "0",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Baseline: flag everything" in stdout
    assert "n = 3 questions (6 answers scored, 0 left out" in stdout

    results = json.loads(output.read_text(encoding="utf-8"))
    assert results["dataset"]["commit"] == ev.TRUTHFULQA_COMMIT
    assert results["answers_scored"] == 6
    assert len(results["items"]) == 6
    # Mock models give no verdict (QUESTIONABLE), so every answer is MEDIUM risk.
    assert results["metrics"]["Flag MEDIUM or worse"]["catch_rate"] == 1.0
    assert results["metrics"]["Flag HIGH or worse"]["catch_rate"] == 0.0
