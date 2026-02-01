# Quick Start Guide

Get MAVEN running in 5 minutes to detect AI hallucinations.

## Installation

```bash
pip install maven-ai
```

Or install from source:

```bash
git clone https://github.com/rwondo/maven.git
cd maven
pip install -e .
```

## Set Up API Keys

MAVEN needs API keys for the models you want to use:

```bash
# For Together AI (Recommended - cost-effective)
export TOGETHER_API_KEY="your-together-key"

# Or use premium models
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"
```

## Basic Example: Detecting Hallucinations

```python
from maven import HallucinationDetector

# Initialize detector with 3 models
detector = HallucinationDetector(
    models=[
        "together/llama-3.1-8b",
        "together/qwen-2.5-7b",
        "together/mixtral-8x7b"
    ]
)

# Check an AI-generated answer for hallucinations
report = detector.detect(
    query="What are the side effects of aspirin?",
    answer="According to the 2023 Johnson Study published in NEJM, aspirin causes...",
    domain="medical"
)

# Check the results
print(f"Risk Level: {report.risk_level}")           # CRITICAL, HIGH, MEDIUM, or LOW
print(f"Confidence: {report.confidence_score}%")    # How confident the answer is safe
print(f"Flags: {report.flags}")                     # Specific issues detected

# Take action based on risk level
if report.risk_level in ["CRITICAL", "HIGH"]:
    print("⚠️  WARNING: High risk of hallucination detected!")
    print("Details:", report.flags)
```

## Understanding Results

The `detect()` method returns a `HallucinationReport` object:

```python
report.risk_level          # CRITICAL, HIGH, MEDIUM, or LOW
report.confidence_score    # 0-100 (higher = more confident answer is accurate)
report.flags               # List of specific issues detected
report.consistency_score   # How well models agreed
report.fact_checks         # Results from fact verification
report.citation_checks     # Results from citation verification
report.model_responses     # What each model said
report.disagreements       # Where models disagreed
```

## Real-World Example: Medical AI Safety

```python
# Your AI generates medical advice
ai_answer = your_ai_model("What conditions prevent aspirin use?")

# Verify before showing to patient
report = detector.detect(
    query="What conditions prevent aspirin use?",
    answer=ai_answer,
    domain="medical"
)

# Block dangerous responses
if report.risk_level == "CRITICAL":
    # Fabricated study or citation detected
    alert_human_expert(report)
    return "Please consult a healthcare professional."
elif report.risk_level == "HIGH":
    # Questionable claims detected
    flag_for_review(report)
    return ai_answer  # With warning label
else:
    # Answer appears safe
    return ai_answer
```

## Configuration Options

```python
detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b", "together/mixtral-8x7b"],
    config={
        "timeout_seconds": 30,      # Per-check timeout
        "enable_tools": True,       # Use Wikipedia/calculator for fact-checking
    }
)
```

## Using Different Models

### Together AI (Recommended - Cost Effective)

```python
# Small models (fast, affordable)
detector = HallucinationDetector(
    models=[
        "together/llama-3.1-8b",
        "together/qwen-2.5-7b",
        "together/mixtral-8x7b"
    ]
)

# Larger models (better accuracy)
detector = HallucinationDetector(
    models=[
        "together/llama-3.3-70b",
        "together/mixtral-8x22b",
        "together/qwen-2.5-72b"
    ]
)
```

### Premium Models (Higher Accuracy)

```python
detector = HallucinationDetector(
    models=[
        "claude-sonnet-4",
        "gpt-4",
        "gemini-pro"
    ]
)
```

### Mixed Approach (Balance Cost & Accuracy)

```python
detector = HallucinationDetector(
    models=[
        "together/llama-3.3-70b",  # Open-source, affordable
        "claude-sonnet-4",         # Premium, high accuracy
        "together/qwen-2.5-72b"    # Open-source, strong reasoning
    ]
)
```

## Important: Detection vs Generation

**MAVEN is for DETECTION, not GENERATION.**

❌ **Don't use for generating answers:**
```python
# This will give worse results than a single model
result = orchestrator.verify("What is 2+2?")  # DON'T DO THIS
```

✅ **Do use for detecting hallucinations:**
```python
# Generate with single model
answer = single_model.generate("What is 2+2?")

# Verify with MAVEN
report = detector.detect(query="What is 2+2?", answer=answer)  # DO THIS
```

## Next Steps

- See [example_hallucination_detection.py](../example_hallucination_detection.py) for complete examples
- Read the [API Reference](API.md) for full documentation
- Check [README.md](../README.md) for benchmark results
- Review [CHANGELOG.md](../CHANGELOG.md) for research findings
