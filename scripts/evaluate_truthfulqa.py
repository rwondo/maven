"""Evaluate the detector on TruthfulQA reference answers.

TruthfulQA (Lin et al., 2021) gives each question a best correct answer and a best
incorrect answer, both written by the dataset authors. This script samples questions
and sends both answers to the detector, so half the items are known to be correct and
half are known to be wrong. No string matching or model judging is needed for labels.

It reports, for two flagging thresholds:
    catch rate        share of wrong answers the detector flagged
    false-alarm rate  share of correct answers the detector flagged
with Wilson 95% intervals, next to a "flag everything" baseline.

Caveat: the reference answers are short and written by people, not by a model, so
these numbers describe performance on clean, known-label answers rather than on real
LLM output.

Usage:
    python scripts/evaluate_truthfulqa.py --n 100
    python scripts/evaluate_truthfulqa.py --n 5 --models mock-a,mock-b   # pipeline check
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
import math
import random
import sys
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from maven import AsyncHallucinationDetector, HallucinationReport, ModelConfigError, __version__

# Pinned to one commit so the questions and answers cannot change between runs.
TRUTHFULQA_COMMIT = "d71c110897f5d31c5d7f309e7bc316c152f6f031"
TRUTHFULQA_URL = (
    f"https://raw.githubusercontent.com/sylinrl/TruthfulQA/{TRUTHFULQA_COMMIT}/TruthfulQA.csv"
)
DEFAULT_MODELS = "together/llama-3.1-8b,together/qwen-2.5-7b,together/mixtral-8x7b"
THRESHOLDS = {
    "Flag MEDIUM or worse": ("MEDIUM", "HIGH", "CRITICAL"),
    "Flag HIGH or worse": ("HIGH", "CRITICAL"),
}
RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


@dataclass(frozen=True)
class Item:
    """One answer to check, with its known label."""

    question: str
    answer: str
    is_hallucination: bool
    category: str


@dataclass(frozen=True)
class Metrics:
    """Confusion counts for one way of flagging answers."""

    caught: int  # wrong answers flagged
    wrong_answers: int
    false_alarms: int  # correct answers flagged
    correct_answers: int

    @property
    def catch_rate(self) -> float:
        return self.caught / self.wrong_answers if self.wrong_answers else float("nan")

    @property
    def false_alarm_rate(self) -> float:
        return self.false_alarms / self.correct_answers if self.correct_answers else float("nan")

    @property
    def accuracy(self) -> float:
        total = self.wrong_answers + self.correct_answers
        right = self.caught + (self.correct_answers - self.false_alarms)
        return right / total if total else float("nan")


def load_rows(url: str = TRUTHFULQA_URL) -> list[dict[str, str]]:
    """Download the TruthfulQA CSV and return its rows."""
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def build_items(rows: list[dict[str, str]], n: int, seed: int) -> list[Item]:
    """Sample n questions and return 2n items: the best correct and best incorrect answer."""
    usable = [r for r in rows if r["Best Answer"].strip() and r["Best Incorrect Answer"].strip()]
    if n > len(usable):
        raise ValueError(f"--n {n} is larger than the {len(usable)} usable questions")
    items = []
    for row in random.Random(seed).sample(usable, n):
        items.append(Item(row["Question"], row["Best Answer"], False, row["Category"]))
        items.append(Item(row["Question"], row["Best Incorrect Answer"], True, row["Category"]))
    return items


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% confidence interval for a proportion (Wilson score method)."""
    if total == 0:
        return (float("nan"), float("nan"))
    p = successes / total
    denominator = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denominator
    half_width = z * math.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominator
    return (max(0.0, centre - half_width), min(1.0, centre + half_width))


def score(labels: list[bool], flagged: list[bool]) -> Metrics:
    """Count catches and false alarms. labels[i] is True for a wrong answer."""
    pairs = list(zip(labels, flagged, strict=True))
    return Metrics(
        caught=sum(1 for wrong, flag in pairs if wrong and flag),
        wrong_answers=sum(1 for wrong, _ in pairs if wrong),
        false_alarms=sum(1 for wrong, flag in pairs if not wrong and flag),
        correct_answers=sum(1 for wrong, _ in pairs if not wrong),
    )


def had_failures(report: HallucinationReport) -> bool:
    """True if any model call failed, so the report does not reflect a full check."""
    return "error" in report.metadata or any(step.error for step in report.trace)


def _rate_cell(count: int, total: int) -> str:
    low, high = wilson_interval(count, total)
    return f"{count}/{total} = {count / total:.0%} ({low:.0%}-{high:.0%})" if total else "n/a"


def format_results(metrics: dict[str, Metrics], risk_counts: dict[str, Counter[str]]) -> str:
    """Markdown tables: rates with 95% intervals, then the risk-level distribution."""
    lines = [
        "| Method | Catch rate (wrong answers flagged) | False-alarm rate (correct answers flagged) | Accuracy |",
        "|---|---|---|---|",
    ]
    for name, m in metrics.items():
        lines.append(
            f"| {name} | {_rate_cell(m.caught, m.wrong_answers)} "
            f"| {_rate_cell(m.false_alarms, m.correct_answers)} | {m.accuracy:.0%} |"
        )
    lines += ["", "| Answer | " + " | ".join(RISK_LEVELS) + " |", "|---|" + "---|" * 4]
    for label, counts in risk_counts.items():
        lines.append(f"| {label} | " + " | ".join(str(counts[r]) for r in RISK_LEVELS) + " |")
    return "\n".join(lines)


async def detect_all(
    items: list[Item], detector: AsyncHallucinationDetector, max_concurrent: int
) -> list[HallucinationReport]:
    def progress(done: int, total: int) -> None:
        print(f"\r  checked {done}/{total}", end="", file=sys.stderr, flush=True)

    reports = await detector.detect_batch(
        [{"query": item.question, "answer": item.answer} for item in items],
        max_concurrent=max_concurrent,
        progress_callback=progress,
    )
    print(file=sys.stderr)
    return reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--n", type=int, default=100, help="questions to sample (default 100)")
    parser.add_argument("--seed", type=int, default=0, help="random seed for the sample")
    parser.add_argument("--models", default=DEFAULT_MODELS, help="comma-separated models")
    parser.add_argument("--max-concurrent", type=int, default=5, help="items checked at once")
    parser.add_argument("--max-concurrent-calls", type=int, help="API calls in flight at once")
    parser.add_argument("--rate-limit-delay", type=float, default=0.5, help="seconds per call")
    parser.add_argument("--output", type=Path, help="JSON results path (default: results/)")
    args = parser.parse_args(argv)

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    items = build_items(load_rows(), args.n, args.seed)
    print(
        f"Checking {len(items)} answers ({args.n} questions x 2) with {len(models)} models: "
        f"about {len(items) * (len(models) + 2)} API calls.",
        file=sys.stderr,
    )

    detector = AsyncHallucinationDetector(
        models=models,
        rate_limit_delay=args.rate_limit_delay,
        max_concurrent_calls=args.max_concurrent_calls,
    )
    try:
        reports = asyncio.run(detect_all(items, detector, args.max_concurrent))
    except ModelConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Items where a model call failed are left out of the scores and counted separately.
    scored = [(i, r) for i, r in zip(items, reports, strict=True) if not had_failures(r)]
    excluded = len(items) - len(scored)
    labels = [item.is_hallucination for item, _ in scored]
    metrics = {
        name: score(labels, [r.risk_level in levels for _, r in scored])
        for name, levels in THRESHOLDS.items()
    }
    metrics["Baseline: flag everything"] = score(labels, [True] * len(labels))
    risk_counts = {
        "Correct (Best Answer)": Counter(r.risk_level for i, r in scored if not i.is_hallucination),
        "Wrong (Best Incorrect Answer)": Counter(
            r.risk_level for i, r in scored if i.is_hallucination
        ),
    }

    print(format_results(metrics, risk_counts))
    print(
        f"\nn = {args.n} questions ({len(scored)} answers scored, {excluded} left out because a "
        f"model call failed); seed {args.seed}; models: {', '.join(models)}; maven {__version__}."
    )

    run_at = datetime.now(UTC)
    output = args.output or Path("results") / f"truthfulqa-{run_at:%Y%m%d-%H%M%S}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "run_at": run_at.isoformat(),
                "maven_version": __version__,
                "dataset": {"name": "TruthfulQA", "commit": TRUTHFULQA_COMMIT},
                "config": {"n_questions": args.n, "seed": args.seed, "models": models},
                "answers_scored": len(scored),
                "answers_excluded": excluded,
                "metrics": {
                    name: {
                        **asdict(m),
                        "catch_rate": m.catch_rate,
                        "false_alarm_rate": m.false_alarm_rate,
                        "accuracy": m.accuracy,
                    }
                    for name, m in metrics.items()
                },
                "items": [
                    {
                        **asdict(item),
                        "risk_level": report.risk_level,
                        "verdicts": report.verdicts,
                        "flags": report.flags,
                        "had_failures": had_failures(report),
                    }
                    for item, report in zip(items, reports, strict=True)
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Results written to {output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
