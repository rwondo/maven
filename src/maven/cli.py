"""
Command-line interface for MAVEN.

This module provides a CLI for running verification queries
from the terminal.

Usage:
    maven "What is the capital of France?"
    maven --models claude-sonnet-4,gpt-4,gemini-pro "Your query"
    maven --config config.json "Your query"
"""

import argparse
import json
import logging
import sys
from typing import List, Optional

from maven import ConsensusOrchestrator, __version__
from maven.consensus import ConsensusResult


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_models(models_str: str) -> List[str]:
    """Parse comma-separated model string."""
    return [m.strip() for m in models_str.split(",") if m.strip()]


def format_result(result: ConsensusResult, verbose: bool = False) -> str:
    """Format verification result for display."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("VERIFICATION RESULT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Consensus: {result.consensus}")
    lines.append(f"Confidence: {result.confidence:.1f}%")
    lines.append(f"Iterations: {result.iterations}")

    if result.dissent:
        lines.append(f"Dissent: {result.dissent}")

    if verbose and result.trace:
        lines.append("")
        lines.append("-" * 60)
        lines.append("VERIFICATION TRACE")
        lines.append("-" * 60)

        for step in result.trace:
            lines.append(f"\n[Iteration {step.iteration}] {step.role.upper()} ({step.model})")
            lines.append(step.summary)

    lines.append("")
    return "\n".join(lines)


def format_json(result: ConsensusResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2, default=str)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="maven",
        description="Multi-Agent Verification & Evaluation Network - "
                    "Reduce AI hallucinations through multi-model consensus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  maven "What is the capital of France?"
  maven --models claude-sonnet-4,gpt-4,gemini-pro "Your query"
  maven --iterations 3 "Complex question here"
  maven --json "Query for JSON output"

Environment Variables:
  ANTHROPIC_API_KEY    API key for Claude models
  OPENAI_API_KEY       API key for GPT models
  GOOGLE_API_KEY       API key for Gemini models
        """,
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="The query to verify",
    )

    parser.add_argument(
        "-m", "--models",
        default="claude-sonnet-4,gpt-4,gemini-pro",
        help="Comma-separated list of models (default: claude-sonnet-4,gpt-4,gemini-pro)",
    )

    parser.add_argument(
        "-i", "--iterations",
        type=int,
        default=5,
        help="Maximum verification iterations (default: 5)",
    )

    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=0.8,
        help="Consensus threshold 0.0-1.0 (default: 0.8)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds per iteration (default: 60)",
    )

    parser.add_argument(
        "-c", "--config",
        help="Path to JSON configuration file",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed trace output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"maven {__version__}",
    )

    return parser


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Check for query
    if not args.query:
        parser.print_help()
        return 1

    setup_logging(args.verbose)

    # Build configuration
    config = {}

    if args.config:
        config = load_config(args.config)

    # CLI args override config file
    config["max_iterations"] = args.iterations
    config["consensus_threshold"] = args.threshold
    config["timeout_seconds"] = args.timeout

    # Parse models
    models = parse_models(args.models)

    if len(models) < 3:
        print("Error: At least 3 models required for consensus", file=sys.stderr)
        return 1

    try:
        # Create orchestrator
        orchestrator = ConsensusOrchestrator(
            models=models,
            config=config,
        )

        # Run verification
        if not args.json:
            print(f"\nVerifying: {args.query}")
            print("Running multi-model verification...")

        result = orchestrator.verify(args.query)

        # Output result
        if args.json:
            print(format_json(result))
        else:
            print(format_result(result, verbose=args.verbose))

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nVerification cancelled.", file=sys.stderr)
        return 130
    except Exception as e:
        logging.exception("Unexpected error")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
