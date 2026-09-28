"""Command-line interface: check one answer for likely hallucinations.

Usage:
    maven --answer "Charlotte Bronte wrote it in 1847." "Who wrote Pride and Prejudice?"
    maven --models together/llama-3.1-8b,gpt-4o --json --answer "..." "question"

Exit codes:
    0  LOW or MEDIUM risk
    1  error (for example a missing API key)
    2  invalid command-line arguments
    3  HIGH or CRITICAL risk
"""

import argparse
import json
import logging
import sys
from typing import Optional

from maven import __version__
from maven.hallucination_detector import HallucinationDetector, HallucinationReport
from maven.models import ModelConfigError

DEFAULT_MODELS = "together/llama-3.1-8b,together/qwen-2.5-7b,together/mixtral-8x7b"
EXIT_HIGH_RISK = 3


def parse_models(models_str: str) -> list[str]:
    """Split a comma-separated model list."""
    return [m.strip() for m in models_str.split(",") if m.strip()]


def create_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="maven",
        description="Ask several LLMs to review an answer and report how likely it is "
        "to contain hallucinations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (set the ones for the providers you use):
  TOGETHER_API_KEY     Together AI models (together/...)
  OPENAI_API_KEY       OpenAI models (gpt-...)
  ANTHROPIC_API_KEY    Anthropic models (claude-...)
  GOOGLE_API_KEY       Google models (gemini-...)
        """,
    )
    parser.add_argument("query", help="the question the answer responds to")
    parser.add_argument("-a", "--answer", required=True, help="the answer to check")
    parser.add_argument(
        "-m",
        "--models",
        default=DEFAULT_MODELS,
        help=f"comma-separated reviewer models, at least 2 (default: {DEFAULT_MODELS})",
    )
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show each model's reply and debug logs"
    )
    parser.add_argument("--version", action="version", version=f"maven {__version__}")
    return parser


def format_report(report: HallucinationReport, verbose: bool = False) -> str:
    """Format a report for the terminal."""
    lines = [
        f"Risk level:     {report.risk_level}",
        f"Verdicts:       {', '.join(report.verdicts)}",
        f"Reliable votes: {report.reliable_share:.0f}% of reviewer models",
    ]

    if report.flags:
        lines.append("Flags:")
        lines.extend(f"  - {flag}" for flag in report.flags)
    else:
        lines.append("Flags:          none")

    if report.disagreements:
        lines.append("Disagreements:")
        lines.extend(f"  - {d}" for d in report.disagreements)

    if verbose:
        for step in report.trace:
            lines.append("")
            lines.append(f"--- {step.role} ({step.model}) ---")
            lines.append(step.content.strip())

    lines.append("")
    if report.risk_level in ("CRITICAL", "HIGH"):
        lines.append("Recommendation: do not rely on this answer without checking it.")
    elif report.risk_level == "MEDIUM":
        lines.append("Recommendation: not enough reviewers rated it RELIABLE; verify key claims.")
    else:
        lines.append("Recommendation: no problems found, but still verify anything important.")
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point. Returns the process exit code."""
    args = create_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        detector = HallucinationDetector(models=parse_models(args.models))
        report = detector.detect(query=args.query, answer=args.answer)
    except (ValueError, ModelConfigError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, default=str))
    else:
        print(format_report(report, verbose=args.verbose))

    return EXIT_HIGH_RISK if report.risk_level in ("CRITICAL", "HIGH") else 0


if __name__ == "__main__":
    sys.exit(main())
