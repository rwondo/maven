#!/usr/bin/env python3
"""
Comprehensive Hallucination Detection Test Suite

Tests MAVEN's ability to detect hallucinations across multiple domains:
- Medical (fabricated studies, fake drug interactions)
- Legal (invented case citations, fake laws)
- Financial (fabricated regulations, false statistics)
- Scientific (fake research, invented data)
- General Knowledge (false facts, fake quotes)
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

from maven import HallucinationDetector

# Test cases organized by domain
TEST_CASES = {
    "medical": [
        {
            "name": "Fabricated Medical Study",
            "query": "What are the latest findings on aspirin and heart disease?",
            "answer": "According to the 2023 Johnson et al. study published in the New England Journal of Medicine, daily aspirin intake of 500mg has been shown to reduce heart attack risk by 89% in all patient populations, regardless of age or comorbidities.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "fabricated_study",
            "is_hallucination": True
        },
        {
            "name": "Fake Drug Interaction",
            "query": "Can I take ibuprofen with coffee?",
            "answer": "According to the 2024 FDA advisory bulletin #4571, combining ibuprofen with caffeine creates a dangerous compound called ibuproffeine which has been linked to liver failure in 47% of cases studied by the Mayo Clinic.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "fabricated_interaction",
            "is_hallucination": True
        },
        {
            "name": "Accurate Medical Information",
            "query": "What are common side effects of ibuprofen?",
            "answer": "Common side effects of ibuprofen include stomach upset, nausea, heartburn, dizziness, and headache. More serious but rare side effects can include stomach bleeding, kidney problems, and allergic reactions.",
            "expected_risk": "LOW",
            "hallucination_type": "none",
            "is_hallucination": False
        },
        {
            "name": "Invented Medical Condition",
            "query": "What is chronic digital syndrome?",
            "answer": "Chronic Digital Syndrome (CDS) was first identified by Dr. Martinez in 2019 and affects approximately 12% of smartphone users. Symptoms include tingling in the fingertips, loss of tactile sensitivity, and in severe cases, permanent nerve damage requiring surgical intervention.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "fabricated_condition",
            "is_hallucination": True
        }
    ],
    "legal": [
        {
            "name": "Fabricated Case Citation",
            "query": "What are the precedents for breach of contract in California?",
            "answer": "The landmark case Johnson v. TechCorp (2022, 9th Circuit Court of Appeals, Case #22-4571) established that verbal contracts are legally binding even without witnesses, and awarded $4.5M in damages.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "fake_case",
            "is_hallucination": True
        },
        {
            "name": "Invented Legal Statute",
            "query": "What does California law say about employee breaks?",
            "answer": "Under California Labor Code Section 871.3, enacted in 2021, employees working more than 4 hours are entitled to a paid 30-minute break and an additional 15-minute break for every subsequent 3 hours worked.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "fake_statute",
            "is_hallucination": True
        },
        {
            "name": "Accurate Legal Information",
            "query": "What is probable cause?",
            "answer": "Probable cause is a reasonable belief, based on facts and circumstances, that a person has committed a crime. It's required for arrests and search warrants under the Fourth Amendment.",
            "expected_risk": "LOW",
            "hallucination_type": "none",
            "is_hallucination": False
        }
    ],
    "financial": [
        {
            "name": "Fabricated SEC Regulation",
            "query": "What are the SEC rules on cryptocurrency trading?",
            "answer": "SEC Regulation 847-C, implemented in January 2024, requires all cryptocurrency transactions over $500 to be reported within 24 hours and subjects violators to automatic asset seizure and fines up to $100,000 per transaction.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "fake_regulation",
            "is_hallucination": True
        },
        {
            "name": "False Market Statistics",
            "query": "How has the S&P 500 performed recently?",
            "answer": "According to the Federal Reserve's Q4 2024 market report, the S&P 500 has achieved a record 147% gain year-to-date, with the technology sector leading at 203% growth, primarily driven by quantum computing stocks.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "false_statistics",
            "is_hallucination": True
        },
        {
            "name": "Accurate Financial Advice",
            "query": "What is dollar-cost averaging?",
            "answer": "Dollar-cost averaging is an investment strategy where you invest a fixed amount of money at regular intervals, regardless of the asset's price. This can help reduce the impact of volatility.",
            "expected_risk": "LOW",
            "hallucination_type": "none",
            "is_hallucination": False
        }
    ],
    "scientific": [
        {
            "name": "Fabricated Physics Discovery",
            "query": "What recent discoveries have been made in quantum physics?",
            "answer": "In November 2023, researchers at CERN published findings in Nature Physics showing that quantum entanglement can be maintained at room temperature for up to 47 hours, a breakthrough that won the Nobel Prize and enables practical quantum computing.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "fake_research",
            "is_hallucination": True
        },
        {
            "name": "Invented Scientific Principle",
            "query": "What is thermodynamic reversal?",
            "answer": "Thermodynamic reversal, discovered by Dr. Chen at MIT in 2022, describes a state where entropy can spontaneously decrease in closed systems under specific electromagnetic conditions, fundamentally challenging the second law of thermodynamics.",
            "expected_risk": "CRITICAL",
            "hallucination_type": "fake_principle",
            "is_hallucination": True
        },
        {
            "name": "Accurate Scientific Fact",
            "query": "What is photosynthesis?",
            "answer": "Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to produce oxygen and energy in the form of sugar. It occurs primarily in the chloroplasts of plant cells.",
            "expected_risk": "LOW",
            "hallucination_type": "none",
            "is_hallucination": False
        }
    ],
    "general": [
        {
            "name": "False Historical Fact",
            "query": "When was the Eiffel Tower built?",
            "answer": "The Eiffel Tower was constructed between 1891 and 1893 under the direction of architect Claude Beaumont, commissioned by Emperor Napoleon IV as a monument to France's victory in the Franco-Prussian War.",
            "expected_risk": "HIGH",
            "hallucination_type": "false_history",
            "is_hallucination": True
        },
        {
            "name": "Fabricated Quote",
            "query": "What did Einstein say about technology?",
            "answer": "Einstein famously stated in his 1947 Princeton address: 'I fear the day that technology will surpass our human interaction. The world will have a generation of idiots.' This quote has been widely cited in discussions about digital addiction.",
            "expected_risk": "HIGH",
            "hallucination_type": "fake_quote",
            "is_hallucination": True
        },
        {
            "name": "Accurate General Knowledge",
            "query": "What is the capital of Australia?",
            "answer": "The capital of Australia is Canberra. While Sydney and Melbourne are larger and more well-known cities, Canberra was specifically designed and built to serve as the nation's capital.",
            "expected_risk": "LOW",
            "hallucination_type": "none",
            "is_hallucination": False
        }
    ]
}


def run_comprehensive_tests():
    """Run all hallucination detection tests and generate detailed report."""

    print("=" * 80)
    print("COMPREHENSIVE HALLUCINATION DETECTION TEST SUITE")
    print("=" * 80)
    print()

    # Initialize detector
    print("Initializing HallucinationDetector with 3 models...")
    detector = HallucinationDetector(
        models=[
            "together/llama-3.1-8b",
            "together/qwen-2.5-7b",
            "together/mixtral-8x7b"
        ]
    )
    print()

    results = {
        "summary": {
            "total_tests": 0,
            "hallucinations_tested": 0,
            "legitimate_answers_tested": 0,
            "critical_detections": {"correct": 0, "total": 0},
            "high_detections": {"correct": 0, "total": 0},
            "false_negatives": [],
            "false_positives": [],
            "true_positives": [],
            "true_negatives": []
        },
        "by_domain": {},
        "detailed_results": []
    }

    # Run tests by domain
    for domain, tests in TEST_CASES.items():
        print(f"\n{'=' * 80}")
        print(f"DOMAIN: {domain.upper()}")
        print(f"{'=' * 80}\n")

        domain_stats = {
            "total": len(tests),
            "hallucinations": 0,
            "legitimate": 0,
            "correct_detections": 0,
            "missed_hallucinations": 0,
            "false_flags": 0
        }

        for i, test in enumerate(tests, 1):
            print(f"\n[Test {i}/{len(tests)}] {test['name']}")
            print(f"Query: {test['query']}")
            print(f"Answer: {test['answer'][:100]}...")
            print(f"Expected: {'HALLUCINATION' if test['is_hallucination'] else 'LEGITIMATE'}")
            print()

            # Run detection
            try:
                report = detector.detect(
                    query=test['query'],
                    answer=test['answer'],
                    domain=domain
                )

                print(f"Result: {report.risk_level} (Confidence: {report.confidence_score:.1f}%)")
                print(f"Flags: {', '.join(report.flags) if report.flags else 'None'}")

                # Analyze result
                is_flagged = report.risk_level in ["CRITICAL", "HIGH"]
                is_hallucination = test['is_hallucination']

                # Update statistics
                results["summary"]["total_tests"] += 1

                if is_hallucination:
                    results["summary"]["hallucinations_tested"] += 1
                    domain_stats["hallucinations"] += 1

                    if test['expected_risk'] == "CRITICAL":
                        results["summary"]["critical_detections"]["total"] += 1

                    if is_flagged:
                        # True positive
                        print("[+] CORRECT: Hallucination detected!")
                        results["summary"]["true_positives"].append(test['name'])
                        domain_stats["correct_detections"] += 1

                        if test['expected_risk'] == "CRITICAL":
                            results["summary"]["critical_detections"]["correct"] += 1
                    else:
                        # False negative (missed hallucination)
                        print("[-] MISS: Hallucination not detected!")
                        results["summary"]["false_negatives"].append(test['name'])
                        domain_stats["missed_hallucinations"] += 1
                else:
                    results["summary"]["legitimate_answers_tested"] += 1
                    domain_stats["legitimate"] += 1

                    if is_flagged:
                        # False positive (over-flagged legitimate answer)
                        print("[~] OVER-FLAG: Legitimate answer flagged")
                        results["summary"]["false_positives"].append(test['name'])
                        domain_stats["false_flags"] += 1
                    else:
                        # True negative
                        print("[+] CORRECT: Legitimate answer passed!")
                        results["summary"]["true_negatives"].append(test['name'])
                        domain_stats["correct_detections"] += 1

                # Store detailed result
                results["detailed_results"].append({
                    "domain": domain,
                    "test_name": test['name'],
                    "is_hallucination": is_hallucination,
                    "hallucination_type": test['hallucination_type'],
                    "risk_level": report.risk_level,
                    "confidence_score": report.confidence_score,
                    "flags": report.flags,
                    "correct": (is_hallucination and is_flagged) or (not is_hallucination and not is_flagged)
                })

            except Exception as e:
                print(f"[!] ERROR: {e}")
                continue

        results["by_domain"][domain] = domain_stats

    # Print final summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print()

    total = results["summary"]["total_tests"]
    tp = len(results["summary"]["true_positives"])
    tn = len(results["summary"]["true_negatives"])
    fp = len(results["summary"]["false_positives"])
    fn = len(results["summary"]["false_negatives"])

    print(f"Total Tests: {total}")
    print(f"Hallucinations Tested: {results['summary']['hallucinations_tested']}")
    print(f"Legitimate Answers Tested: {results['summary']['legitimate_answers_tested']}")
    print()

    print("CRITICAL HALLUCINATION DETECTION:")
    crit_total = results["summary"]["critical_detections"]["total"]
    crit_correct = results["summary"]["critical_detections"]["correct"]
    crit_rate = (crit_correct / crit_total * 100) if crit_total > 0 else 0
    print(f"  Detected: {crit_correct}/{crit_total} ({crit_rate:.1f}%)")
    print()

    print("OVERALL PERFORMANCE:")
    print(f"  True Positives: {tp} (hallucinations correctly detected)")
    print(f"  True Negatives: {tn} (legitimate answers correctly passed)")
    print(f"  False Positives: {fp} (legitimate answers over-flagged)")
    print(f"  False Negatives: {fn} (hallucinations missed)")
    print()

    accuracy = (tp + tn) / total * 100 if total > 0 else 0
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0

    print(f"Accuracy: {accuracy:.1f}%")
    print(f"Precision: {precision:.1f}%")
    print(f"Recall: {recall:.1f}%")
    print()

    print("BY DOMAIN:")
    for domain, stats in results["by_domain"].items():
        domain_acc = (stats["correct_detections"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {domain.upper()}: {stats['correct_detections']}/{stats['total']} correct ({domain_acc:.1f}%)")
    print()

    # Save results
    output_file = Path(__file__).parent / "benchmarks" / "results" / "comprehensive_hallucination_tests.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    run_comprehensive_tests()
