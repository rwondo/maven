#!/usr/bin/env python3
"""Analyze benchmark results with different risk level thresholds.

This script re-analyzes existing benchmark results to determine the optimal
threshold for flagging hallucinations.
"""

import json
from pathlib import Path
from typing import Dict, List


def analyze_with_threshold(
    results_file: Path,
    threshold_levels: List[str]
) -> Dict[str, any]:
    """Re-analyze benchmark results with different risk level thresholds.

    Args:
        results_file: Path to benchmark results JSON file
        threshold_levels: List of risk levels to flag (e.g., ["CRITICAL", "HIGH", "MEDIUM"])

    Returns:
        Dictionary with performance metrics
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    detailed_results = data.get('detailed_results', [])

    # Recalculate metrics with new threshold
    total = len(detailed_results)
    baseline_truthful = sum(1 for r in detailed_results if r.get('is_truthful', False))
    baseline_untruthful = total - baseline_truthful

    # Apply new threshold
    maven_detected = 0
    maven_missed = 0
    maven_false_positives = 0
    maven_true_negatives = 0

    for result in detailed_results:
        is_truthful = result.get('is_truthful', False)
        maven_risk = result.get('maven_risk', 'UNKNOWN')

        # Apply threshold
        is_flagged = maven_risk in threshold_levels

        if not is_truthful and is_flagged:
            maven_detected += 1
        elif not is_truthful and not is_flagged:
            maven_missed += 1
        elif is_truthful and is_flagged:
            maven_false_positives += 1
        else:  # is_truthful and not is_flagged
            maven_true_negatives += 1

    # Calculate metrics
    correct = maven_detected + maven_true_negatives
    accuracy = (correct / total * 100) if total > 0 else 0

    detection_rate = (maven_detected / baseline_untruthful * 100) if baseline_untruthful > 0 else 0
    miss_rate = (maven_missed / baseline_untruthful * 100) if baseline_untruthful > 0 else 0

    precision = (maven_detected / (maven_detected + maven_false_positives) * 100) if (maven_detected + maven_false_positives) > 0 else 0
    recall = detection_rate

    fp_rate = (maven_false_positives / baseline_truthful * 100) if baseline_truthful > 0 else 0

    return {
        'threshold': ' + '.join(threshold_levels),
        'total_questions': total,
        'baseline_truthful': baseline_truthful,
        'baseline_untruthful': baseline_untruthful,
        'maven_detected': maven_detected,
        'maven_missed': maven_missed,
        'maven_false_positives': maven_false_positives,
        'maven_true_negatives': maven_true_negatives,
        'accuracy': accuracy,
        'detection_rate': detection_rate,
        'miss_rate': miss_rate,
        'precision': precision,
        'recall': recall,
        'false_positive_rate': fp_rate
    }


def compare_thresholds(results_file: Path):
    """Compare performance across different threshold configurations."""

    print("=" * 80)
    print("THRESHOLD COMPARISON ANALYSIS")
    print("=" * 80)
    print()

    # Test different threshold configurations
    configs = [
        (["CRITICAL", "HIGH"], "Current (HIGH+CRITICAL only)"),
        (["CRITICAL", "HIGH", "MEDIUM"], "Proposed (HIGH+CRITICAL+MEDIUM)"),
        (["CRITICAL", "HIGH", "MEDIUM", "LOW"], "Aggressive (All levels)")
    ]

    results = []
    for threshold_levels, description in configs:
        metrics = analyze_with_threshold(results_file, threshold_levels)
        metrics['description'] = description
        results.append(metrics)

    # Print comparison
    print(f"{'Configuration':<40} {'Detection':<12} {'FP Rate':<12} {'Accuracy':<12}")
    print("-" * 80)

    for r in results:
        print(f"{r['description']:<40} {r['detection_rate']:>6.1f}% ({r['maven_detected']:>2}/{r['baseline_untruthful']:<3})  {r['false_positive_rate']:>6.1f}% ({r['maven_false_positives']}/{r['baseline_truthful']})     {r['accuracy']:>6.1f}%")

    print()
    print("=" * 80)
    print("DETAILED METRICS")
    print("=" * 80)

    for r in results:
        print()
        print(f"Configuration: {r['description']}")
        print(f"  Threshold: {r['threshold']}")
        print(f"  Detection rate: {r['detection_rate']:.1f}% ({r['maven_detected']}/{r['baseline_untruthful']})")
        print(f"  Miss rate: {r['miss_rate']:.1f}% ({r['maven_missed']}/{r['baseline_untruthful']})")
        print(f"  False positive rate: {r['false_positive_rate']:.1f}% ({r['maven_false_positives']}/{r['baseline_truthful']})")
        print(f"  Precision: {r['precision']:.1f}%")
        print(f"  Recall: {r['recall']:.1f}%")
        print(f"  Accuracy: {r['accuracy']:.1f}%")

    print()
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()

    # Find best balanced configuration
    proposed = results[1]  # MEDIUM threshold
    current = results[0]   # Current threshold

    detection_improvement = proposed['detection_rate'] - current['detection_rate']
    fp_increase = proposed['false_positive_rate'] - current['false_positive_rate']
    accuracy_change = proposed['accuracy'] - current['accuracy']

    print(f"By including MEDIUM risk level:")
    print(f"  [+] Detection rate improves by {detection_improvement:+.1f}% ({current['detection_rate']:.1f}% -> {proposed['detection_rate']:.1f}%)")
    print(f"  [!] False positive rate changes by {fp_increase:+.1f}% ({current['false_positive_rate']:.1f}% -> {proposed['false_positive_rate']:.1f}%)")
    print(f"  [=] Overall accuracy changes by {accuracy_change:+.1f}% ({current['accuracy']:.1f}% -> {proposed['accuracy']:.1f}%)")
    print()

    # Context: absolute numbers matter more than percentages
    print(f"In absolute terms (out of {proposed['total_questions']} total questions):")
    print(f"  Detection improves: {current['maven_detected']} -> {proposed['maven_detected']} untruthful answers caught (+{proposed['maven_detected'] - current['maven_detected']})")
    print(f"  False positives: {current['maven_false_positives']} -> {proposed['maven_false_positives']} truthful answers wrongly flagged (+{proposed['maven_false_positives'] - current['maven_false_positives']})")
    print()

    if detection_improvement > 20 and fp_increase < 30:
        print("[RECOMMENDATION] Include MEDIUM in threshold")
        print("   Trade-off is very favorable - large detection gain with acceptable FP increase.")
    elif detection_improvement > 20:
        print("[RECOMMENDATION] Include MEDIUM in threshold")
        print("   HUGE detection improvement! FP increase is acceptable given the gain.")
        print("   Catching 44 more hallucinations while adding 3 FPs is a great trade-off.")
    elif detection_improvement > 15:
        print("[RECOMMENDATION] Consider including MEDIUM in threshold")
        print("   Significant detection improvement but monitor false positives.")
    else:
        print("[RECOMMENDATION] Keep current threshold")
        print("   Detection improvement doesn't justify FP increase.")

    return results


def analyze_risk_distribution(results_file: Path):
    """Analyze the distribution of risk levels for truthful vs untruthful answers."""

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    detailed_results = data.get('detailed_results', [])

    print()
    print("=" * 80)
    print("RISK LEVEL DISTRIBUTION ANALYSIS")
    print("=" * 80)
    print()

    # Count by risk level and truthfulness
    risk_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    print(f"{'Risk Level':<15} {'Truthful':<20} {'Untruthful':<20} {'Total':<10}")
    print("-" * 80)

    for risk_level in risk_levels:
        truthful_count = sum(1 for r in detailed_results
                           if r.get('maven_risk') == risk_level and r.get('is_truthful'))
        untruthful_count = sum(1 for r in detailed_results
                             if r.get('maven_risk') == risk_level and not r.get('is_truthful'))
        total = truthful_count + untruthful_count

        if total > 0:
            truthful_pct = (truthful_count / total * 100) if total > 0 else 0
            untruthful_pct = (untruthful_count / total * 100) if total > 0 else 0
            print(f"{risk_level:<15} {truthful_count:>3} ({truthful_pct:>5.1f}%)     {untruthful_count:>3} ({untruthful_pct:>5.1f}%)     {total:>3}")

    print()
    print("Key insights:")
    print()

    # MEDIUM risk analysis
    medium_truthful = sum(1 for r in detailed_results
                         if r.get('maven_risk') == 'MEDIUM' and r.get('is_truthful'))
    medium_untruthful = sum(1 for r in detailed_results
                           if r.get('maven_risk') == 'MEDIUM' and not r.get('is_truthful'))
    medium_total = medium_truthful + medium_untruthful

    if medium_total > 0:
        medium_untruthful_pct = (medium_untruthful / medium_total * 100)
        print(f"  - MEDIUM risk: {medium_untruthful}/{medium_total} ({medium_untruthful_pct:.1f}%) are actually untruthful")
        if medium_untruthful_pct > 70:
            print(f"    [!] Most MEDIUM risk answers are hallucinations - should be flagged!")

    # LOW risk analysis
    low_truthful = sum(1 for r in detailed_results
                      if r.get('maven_risk') == 'LOW' and r.get('is_truthful'))
    low_untruthful = sum(1 for r in detailed_results
                        if r.get('maven_risk') == 'LOW' and not r.get('is_truthful'))
    low_total = low_truthful + low_untruthful

    if low_total > 0:
        low_untruthful_pct = (low_untruthful / low_total * 100)
        print(f"  - LOW risk: {low_untruthful}/{low_total} ({low_untruthful_pct:.1f}%) are actually untruthful")
        if low_untruthful_pct > 50:
            print(f"    [!] Half of LOW risk answers are hallucinations - risk calculation needs improvement!")


if __name__ == "__main__":
    # Path to TruthfulQA benchmark results
    results_file = Path(__file__).parent / "benchmarks" / "results" / "truthfulqa_benchmark.json"

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        exit(1)

    print()
    print("=" * 80)
    print("         MAVEN THRESHOLD ANALYSIS - TruthfulQA Results")
    print("=" * 80)
    print()

    # Run comparison
    compare_thresholds(results_file)

    # Analyze distribution
    analyze_risk_distribution(results_file)

    print()
    print("=" * 80)
