#!/usr/bin/env python3
"""
Comprehensive Benchmark Suite for MAVEN

Runs all benchmarks to generate publication-ready results.
Total estimated cost: ~$1.50 with full datasets.

Benchmarks included:
1. TruthfulQA (50 questions - adjustable)
2. HaluEval (50 samples - adjustable)
3. Hallucination Reduction comparison

Budget options:
- MINIMAL: 30 total tests (~$0.03)
- STANDARD: 110 total tests (~$0.10)
- COMPREHENSIVE: 917 total tests (~$0.35)
- MAXIMUM: Full datasets (~$1.50)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import argparse

# Configuration for different budget levels
BUDGET_CONFIGS = {
    "minimal": {
        "truthfulqa_limit": 10,
        "halueval_limit": 10,
        "hallucination_reduction_limit": 10,
        "estimated_cost": "$0.03",
        "description": "Quick validation test"
    },
    "standard": {
        "truthfulqa_limit": 25,
        "halueval_limit": 25,
        "hallucination_reduction_limit": 10,
        "estimated_cost": "$0.05",
        "description": "Good for documentation"
    },
    "comprehensive": {
        "truthfulqa_limit": 100,
        "halueval_limit": 50,
        "hallucination_reduction_limit": 10,
        "estimated_cost": "$0.18",
        "description": "Strong statistical evidence"
    },
    "maximum": {
        "truthfulqa_limit": 400,  # Half of full dataset (817/2)
        "halueval_limit": 50,
        "hallucination_reduction_limit": 10,
        "estimated_cost": "$0.75",
        "description": "Large benchmark suite (50% of full dataset)"
    }
}


def print_banner():
    """Print welcome banner."""
    print("""
    ================================================================================
                      MAVEN COMPREHENSIVE BENCHMARK SUITE
    ================================================================================

    Testing hallucination detection against famous benchmarks:
    - TruthfulQA (Lin et al., 2021)
    - HaluEval (Li et al., 2023)
    - Hallucination Reduction Analysis

    ================================================================================
    """)


def select_budget_tier():
    """Interactive budget tier selection."""
    print("\nAvailable Budget Tiers:")
    print("=" * 80)

    for i, (tier, config) in enumerate(BUDGET_CONFIGS.items(), 1):
        total_tests = (config["truthfulqa_limit"] +
                      config["halueval_limit"] +
                      config["hallucination_reduction_limit"])
        print(f"{i}. {tier.upper()}")
        print(f"   Cost: {config['estimated_cost']}")
        print(f"   Tests: {total_tests} total")
        print(f"   Description: {config['description']}")
        print()

    choice = input("Select budget tier (1-4) or press Enter for STANDARD: ").strip()

    if not choice:
        return "standard"

    tier_map = {
        "1": "minimal",
        "2": "standard",
        "3": "comprehensive",
        "4": "maximum"
    }

    return tier_map.get(choice, "standard")


def run_truthfulqa(limit: int):
    """Run TruthfulQA benchmark."""
    print("\n" + "=" * 80)
    print(f"RUNNING TRUTHFULQA BENCHMARK (limit={limit})")
    print("=" * 80)

    # Modify the benchmark file temporarily
    benchmark_file = Path(__file__).parent / "benchmark_truthfulqa.py"

    # Read the file
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the limit
    content = content.replace('limit=50', f'limit={limit}')

    # Write temporary modified file
    temp_file = Path(__file__).parent / "benchmark_truthfulqa_temp.py"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # Run the benchmark
    try:
        os.system(f'python "{temp_file}"')
    finally:
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()


def run_halueval(limit: int):
    """Run HaluEval benchmark."""
    print("\n" + "=" * 80)
    print(f"RUNNING HALUEVAL BENCHMARK (limit={limit})")
    print("=" * 80)

    # For HaluEval, we're using the embedded samples
    # So we just run it directly (it has 10 samples by default)
    benchmark_file = Path(__file__).parent / "benchmark_halueval.py"

    if limit <= 10:
        # Just run as-is
        os.system(f'python "{benchmark_file}"')
    else:
        print(f"Note: HaluEval benchmark currently has 10 embedded samples.")
        print(f"For full dataset ({limit} samples), download from:")
        print("https://github.com/RUCAIBox/HaluEval")
        print("\nRunning with available 10 samples...")
        os.system(f'python "{benchmark_file}"')


def run_hallucination_reduction():
    """Run hallucination reduction benchmark."""
    print("\n" + "=" * 80)
    print("RUNNING HALLUCINATION REDUCTION BENCHMARK")
    print("=" * 80)

    benchmark_file = Path(__file__).parent / "benchmark_hallucination_reduction.py"
    os.system(f'python "{benchmark_file}"')


def generate_combined_report(tier: str):
    """Generate a combined report from all benchmark results."""
    print("\n" + "=" * 80)
    print("GENERATING COMBINED REPORT")
    print("=" * 80)

    results_dir = Path(__file__).parent / "benchmarks" / "results"
    combined_results = {
        "benchmark_suite": "MAVEN Comprehensive Evaluation",
        "timestamp": datetime.now().isoformat(),
        "budget_tier": tier,
        "config": BUDGET_CONFIGS[tier],
        "benchmarks": {}
    }

    # Load TruthfulQA results
    truthfulqa_file = results_dir / "truthfulqa_benchmark.json"
    if truthfulqa_file.exists():
        with open(truthfulqa_file, 'r', encoding='utf-8') as f:
            combined_results["benchmarks"]["truthfulqa"] = json.load(f)

    # Load HaluEval results
    halueval_file = results_dir / "halueval_benchmark.json"
    if halueval_file.exists():
        with open(halueval_file, 'r', encoding='utf-8') as f:
            combined_results["benchmarks"]["halueval"] = json.load(f)

    # Load Hallucination Reduction results
    reduction_file = results_dir / "hallucination_reduction_benchmark.json"
    if reduction_file.exists():
        with open(reduction_file, 'r', encoding='utf-8') as f:
            combined_results["benchmarks"]["hallucination_reduction"] = json.load(f)

    # Calculate overall metrics
    combined_results["overall_metrics"] = calculate_overall_metrics(combined_results["benchmarks"])

    # Save combined report
    output_file = results_dir / f"combined_benchmark_report_{tier}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, indent=2)

    print(f"\n✅ Combined report saved to: {output_file}")

    # Print summary
    print_summary(combined_results)


def calculate_overall_metrics(benchmarks: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall metrics across all benchmarks."""
    metrics = {
        "total_tests": 0,
        "total_hallucinations_detected": 0,
        "total_false_positives": 0,
        "overall_detection_rate": 0.0,
        "overall_accuracy": 0.0
    }

    # TruthfulQA
    if "truthfulqa" in benchmarks:
        tq = benchmarks["truthfulqa"]
        metrics["total_tests"] += tq.get("total_questions", 0)
        metrics["total_hallucinations_detected"] += tq.get("maven_detected", 0)
        metrics["total_false_positives"] += tq.get("maven_false_positives", 0)

    # HaluEval
    if "halueval" in benchmarks:
        he = benchmarks["halueval"]
        metrics["total_tests"] += he.get("total_samples", 0)
        metrics["total_hallucinations_detected"] += he.get("hallucinations_detected", 0)

    # Hallucination Reduction
    if "hallucination_reduction" in benchmarks:
        hr = benchmarks["hallucination_reduction"]["summary"]
        metrics["total_tests"] += hr.get("total_questions", 0)
        metrics["total_hallucinations_detected"] += hr.get("maven_detected", 0)
        metrics["total_false_positives"] += hr.get("false_positives", 0)

    return metrics


def print_summary(combined_results: Dict[str, Any]):
    """Print summary of all benchmarks."""
    print("\n" + "=" * 80)
    print("MAVEN BENCHMARK SUITE - SUMMARY")
    print("=" * 80)
    print()

    tier = combined_results["budget_tier"]
    config = combined_results["config"]

    print(f"Budget Tier: {tier.upper()}")
    print(f"Estimated Cost: {config['estimated_cost']}")
    print()

    benchmarks = combined_results["benchmarks"]

    # TruthfulQA
    if "truthfulqa" in benchmarks:
        tq = benchmarks["truthfulqa"]
        print("📊 TruthfulQA Results:")
        print(f"   Questions tested: {tq.get('total_questions', 0)}")
        print(f"   Accuracy: {tq.get('accuracy', 0):.1f}%")
        if tq.get('baseline_untruthful', 0) > 0:
            detection_rate = (tq.get('maven_detected', 0) / tq.get('baseline_untruthful', 1)) * 100
            print(f"   Detection rate: {detection_rate:.1f}%")
        print()

    # HaluEval
    if "halueval" in benchmarks:
        he = benchmarks["halueval"]
        print("📊 HaluEval Results:")
        print(f"   Samples tested: {he.get('total_samples', 0)}")
        print(f"   Detection rate: {he.get('detection_rate', 0):.1f}%")
        print(f"   Perfect results: {he.get('perfect', 0)}/{he.get('total_samples', 0)}")
        print()

    # Hallucination Reduction
    if "hallucination_reduction" in benchmarks:
        hr = benchmarks["hallucination_reduction"]["summary"]
        print("📊 Hallucination Reduction:")
        print(f"   Reduction rate: {hr.get('reduction_rate', 0):.1f}%")
        print(f"   Accuracy: {hr.get('accuracy', 0):.1f}%")
        print()

    # Overall
    overall = combined_results["overall_metrics"]
    print("🎯 OVERALL METRICS:")
    print(f"   Total tests run: {overall['total_tests']}")
    print(f"   Total hallucinations caught: {overall['total_hallucinations_detected']}")
    print(f"   False positives: {overall['total_false_positives']}")
    print()

    print("=" * 80)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run MAVEN benchmark suite")
    parser.add_argument(
        "--tier",
        choices=["minimal", "standard", "comprehensive", "maximum"],
        help="Budget tier to use (skip interactive selection)"
    )
    parser.add_argument(
        "--skip-truthfulqa",
        action="store_true",
        help="Skip TruthfulQA benchmark"
    )
    parser.add_argument(
        "--skip-halueval",
        action="store_true",
        help="Skip HaluEval benchmark"
    )
    parser.add_argument(
        "--skip-reduction",
        action="store_true",
        help="Skip Hallucination Reduction benchmark"
    )

    args = parser.parse_args()

    print_banner()

    # Select budget tier
    if args.tier:
        tier = args.tier
        print(f"\nUsing budget tier: {tier.upper()}")
    else:
        tier = select_budget_tier()

    config = BUDGET_CONFIGS[tier]

    print(f"\nSelected: {tier.upper()}")
    print(f"Estimated cost: {config['estimated_cost']}")
    print(f"Description: {config['description']}")
    print()

    confirm = input("Proceed with benchmarks? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Run benchmarks
    start_time = datetime.now()

    if not args.skip_truthfulqa:
        run_truthfulqa(config["truthfulqa_limit"])

    if not args.skip_halueval:
        run_halueval(config["halueval_limit"])

    if not args.skip_reduction:
        run_hallucination_reduction()

    # Generate combined report
    generate_combined_report(tier)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n✅ All benchmarks completed in {duration:.1f} seconds")
    print(f"\nResults saved in: benchmarks/results/")


if __name__ == "__main__":
    main()
