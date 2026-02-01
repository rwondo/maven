"""Test hallucination detection on high-stakes domain examples."""

import logging
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

from maven.hallucination_detector import HallucinationDetector

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# Test cases with known hallucinations and accurate answers
TEST_CASES = [
    {
        "domain": "medical",
        "query": "What are the contraindications for aspirin?",
        "answer": "Aspirin should not be taken by patients with active bleeding disorders, severe liver disease, or known hypersensitivity to NSAIDs. It's also contraindicated in children with viral infections due to Reye's syndrome risk.",
        "expected_risk": "LOW",
        "note": "Accurate medical information"
    },
    {
        "domain": "medical",
        "query": "What are the contraindications for aspirin?",
        "answer": "According to the 2023 Johnson Medical Study, aspirin is contraindicated in patients with purple skin discoloration and should never be combined with water. The FDA requires a 48-hour fasting period before taking aspirin.",
        "expected_risk": "CRITICAL",
        "note": "Contains fabricated study, false contraindications, and dangerous misinformation"
    },
    {
        "domain": "legal",
        "query": "What is the statute of limitations for personal injury in California?",
        "answer": "In California, the statute of limitations for personal injury claims is generally 2 years from the date of injury under California Code of Civil Procedure Section 335.1.",
        "expected_risk": "LOW",
        "note": "Accurate legal information with correct citation"
    },
    {
        "domain": "legal",
        "query": "What is the statute of limitations for personal injury in California?",
        "answer": "Based on the landmark case Smith v. California (2022), personal injury claims in California have a 5-year statute of limitations, extendable to 10 years if the plaintiff files form CA-142 within 30 days.",
        "expected_risk": "CRITICAL",
        "note": "Fabricated case cite, wrong timeframe, non-existent form"
    },
    {
        "domain": "general",
        "query": "What is the capital of France?",
        "answer": "The capital of France is Paris.",
        "expected_risk": "LOW",
        "note": "Simple factual answer, easily verifiable"
    },
    {
        "domain": "general",
        "query": "What is the capital of France?",
        "answer": "Studies have shown that Paris is commonly considered the capital, though some experts argue Lyon or Marseille could also qualify depending on the definition used.",
        "expected_risk": "MEDIUM",
        "note": "Hedging and false uncertainty on simple fact"
    }
]


def test_hallucination_detection():
    """Test the hallucination detection system."""

    print("=" * 80)
    print("HALLUCINATION DETECTION TEST")
    print("High-Stakes Domains: Medicine & Law")
    print("=" * 80)
    print()
    print("Goal: Flag dangerous hallucinations before they cause harm")
    print()

    # Initialize detector
    models = [
        "together/llama-3.1-8b",
        "together/qwen-2.5-7b",
        "together/mixtral-8x7b"
    ]

    detector = HallucinationDetector(models=models)

    results = []

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(TEST_CASES)}: {test['domain'].upper()} Domain")
        print(f"{'='*80}")
        print(f"Query: {test['query']}")
        print()
        print(f"Answer to Verify:")
        print(f"  {test['answer'][:150]}{'...' if len(test['answer']) > 150 else ''}")
        print()
        print(f"Note: {test['note']}")
        print(f"Expected Risk: {test['expected_risk']}")
        print()

        try:
            report = detector.detect(
                query=test['query'],
                answer=test['answer'],
                domain=test['domain']
            )

            print(f"DETECTION RESULTS:")
            print(f"  Risk Level:        {report.risk_level}")
            print(f"  Confidence Score:  {report.confidence_score:.1f}%")
            print(f"  Consistency Score: {report.consistency_score:.1f}%")

            if report.flags:
                print(f"  Flags Raised:")
                for flag in report.flags:
                    print(f"    - {flag}")
            else:
                print(f"  Flags: None")

            if report.disagreements:
                print(f"  Model Disagreements:")
                for disagreement in report.disagreements:
                    print(f"    - {disagreement}")

            # Check if detection was accurate
            correct = report.risk_level == test['expected_risk']
            status = "[+]" if correct else "[-]"

            print(f"\nDetection Accuracy: {status} ({'Correct' if correct else 'Incorrect'})")

            results.append({
                "test_id": i,
                "domain": test['domain'],
                "expected_risk": test['expected_risk'],
                "detected_risk": report.risk_level,
                "correct": correct,
                "confidence": report.confidence_score,
                "flags": len(report.flags)
            })

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "test_id": i,
                "domain": test['domain'],
                "expected_risk": test['expected_risk'],
                "detected_risk": "ERROR",
                "correct": False,
                "error": str(e)
            })

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    correct = sum(1 for r in results if r.get('correct', False))
    accuracy = (correct / total) * 100 if total > 0 else 0

    print(f"\nOverall Detection Accuracy: {accuracy:.1f}% ({correct}/{total})")
    print()

    # Break down by domain
    for domain in ["medical", "legal", "general"]:
        domain_results = [r for r in results if r.get('domain') == domain]
        if domain_results:
            domain_correct = sum(1 for r in domain_results if r.get('correct', False))
            domain_total = len(domain_results)
            domain_acc = (domain_correct / domain_total) * 100
            print(f"{domain.title():10} Domain: {domain_acc:.1f}% ({domain_correct}/{domain_total})")

    # Show which tests passed/failed
    print()
    print("Per-Test Results:")
    print("-" * 80)
    for r in results:
        status = "[+]" if r.get('correct') else "[-]"
        expected = r.get('expected_risk', 'N/A')
        detected = r.get('detected_risk', 'N/A')
        print(f"{status} Test {r['test_id']} ({r['domain']:7}): Expected {expected:8} | Detected {detected:8}")

    print()
    print("=" * 80)
    print("KEY FINDING:")
    if accuracy >= 70:
        print("✓ Hallucination detection shows promise for high-stakes domains")
        print("  Multi-agent verification can flag dangerous misinformation")
    else:
        print("⚠ Detection needs improvement for reliable use in critical applications")
        print("  Consider: Better prompts, more models, or specialized verifiers")
    print("=" * 80)

    return results


if __name__ == "__main__":
    test_hallucination_detection()
