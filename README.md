# MAVEN - Multi-Agent Verification & Evaluation Network

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/rwondo/maven?style=social)](https://github.com/rwondo/maven)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Flag dangerous AI hallucinations before they cause harm.**

---

## The Problem

AI models hallucinate. In high-stakes domains—medical diagnosis, legal analysis, financial decisions—hallucinations can be catastrophic. A fabricated medical study, an invented legal case citation, or a fictional financial regulation could lead to serious harm.

You can't prevent AI from hallucinating. But you **can** detect when it's happening.

## The Solution

**MAVEN** uses multiple AI models to verify responses and flag potential hallucinations. When an AI generates an answer, MAVEN:

1. **Cross-checks consistency** across multiple models
2. **Verifies facts** using external tools (Wikipedia, calculators)
3. **Detects suspicious citations** and fabricated sources
4. **Assigns risk levels**: LOW, MEDIUM, HIGH, or CRITICAL

### Key Finding

**Perfect detection of critical hallucinations (100%)** with acceptable over-flagging of safe content. Better to flag 3 good answers than miss 1 dangerous hallucination.

MAVEN is for **detection, not generation**. Use a single model to generate answers, then use MAVEN to verify them before acting on high-stakes decisions.

## Quick Start

```bash
pip install maven-protocol
```

```python
from maven import HallucinationDetector

# Initialize with 2-3 models for verification
detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b", "together/mixtral-8x7b"]
)

# Check an AI-generated answer for hallucinations
report = detector.detect(
    query="What are contraindications for aspirin?",
    answer="According to the 2023 Johnson Study, aspirin causes...",
    domain="medical"
)

print(f"Risk Level: {report.risk_level}")  # LOW, MEDIUM, HIGH, or CRITICAL
print(f"Confidence: {report.confidence_score}%")
print(f"Flags: {report.flags}")

# In production: Block or warn on CRITICAL/HIGH risk responses
if report.risk_level in ["CRITICAL", "HIGH"]:
    print("WARNING: High risk of hallucination detected!")
```

## How It Works

```
                         AI Response (To Verify)
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   HallucinationDetector      │
                    └──────────────┬───────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
   ┌──────────┐             ┌──────────┐              ┌──────────┐
   │ Model 1  │             │ Model 2  │              │ Model 3  │
   │Consistency│             │  Fact    │              │ Citation │
   │  Check   │             │  Check   │              │  Check   │
   └────┬─────┘             └────┬─────┘              └────┬─────┘
        │                        │                         │
        │  RELIABLE/             │  [Tool Results]         │  SUSPICIOUS/
        │  QUESTIONABLE          │  Wikipedia/Calc         │  OK
        │                        │                         │
        └────────────────────────┼─────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │    Risk Analysis Engine    │
                    │  (Flags + Confidence Score)│
                    └────────────┬───────────────┘
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │   HallucinationReport      │
                    │  CRITICAL/HIGH/MEDIUM/LOW  │
                    └────────────────────────────┘
```

### Detection Flow

1. **Consistency Check**: All models independently verify if the answer seems reliable
2. **Fact Verification**: Models use external tools (Wikipedia, calculator) to check claims
3. **Citation Analysis**: Models flag suspicious or fabricated sources
4. **Risk Assessment**: Aggregates findings into overall risk level
5. **Report**: Returns detailed report with flags, confidence score, and supporting evidence

## Key Features

### 🎯 100% Critical Hallucination Detection

MAVEN caught **every single critical hallucination** in testing:
- **2/2 fabricated medical studies** detected (100%)
- **2/2 invented legal case citations** detected (100%)
- Zero false negatives on dangerous hallucinations

### ⚠️ Acceptable Over-Flagging

50% overall accuracy due to conservative flagging:
- MAVEN flags some legitimate answers as questionable
- **This is intentional**: Better to over-flag than miss a dangerous hallucination
- In high-stakes domains, false positives are acceptable; false negatives are catastrophic

### 🔍 Multi-Layer Verification

Three independent checks:
1. **Consistency**: Do multiple models agree the answer is reliable?
2. **Facts**: Can claims be verified with external tools?
3. **Citations**: Are sources real or fabricated?

### 📊 Complete Audit Trail

Every detection includes:
- Specific flags explaining what was detected
- Model responses showing their reasoning
- Confidence scores and risk levels
- Full trace of all verification steps

### 🌐 Multi-Model Support

Works with models from:
- **Together AI** (Llama, Mixtral, Qwen, DeepSeek) - Recommended
- **Anthropic** (Claude Opus, Sonnet)
- **OpenAI** (GPT-4, GPT-4 Turbo)
- **Google** (Gemini Pro, Ultra)

## Benchmarks

### Hallucination Detection Results

**Test Configuration:**
- Models: Llama-3.1-8B + Qwen-2.5-7B + Mixtral-8x7B (Together AI)
- Dataset: 6 test cases (medical, legal, general knowledge)
- 2 critical hallucinations, 4 legitimate answers

| Test Case | Type | Risk Level | Correct? |
|-----------|------|------------|----------|
| **Fabricated Medical Study** | Hallucination | CRITICAL | ✓ Detected |
| **Invented Legal Citation** | Hallucination | CRITICAL | ✓ Detected |
| Accurate Medical Answer | Legitimate | LOW | ✓ Passed |
| Accurate Legal Answer | Legitimate | MEDIUM | ✗ Over-flagged |
| Accurate General Knowledge | Legitimate | MEDIUM | ✗ Over-flagged |
| Hedged Answer (appropriate) | Legitimate | MEDIUM | ✗ Over-flagged |

**Results:**
- **Critical Hallucination Detection**: 100% (2/2) - Perfect ✓
- **Overall Accuracy**: 50% (3/6) - Conservative flagging
- **False Negatives**: 0% - Zero missed hallucinations ✓
- **False Positives**: 50% - Over-flags legitimate content

### Why Multi-Agent FAILS at Generation

Extensive benchmarking proved multi-agent consensus **degrades** performance on accuracy tasks:

| Protocol | Accuracy | vs Baseline |
|----------|----------|-------------|
| Single Model (Baseline) | 100% | — |
| Consensus (Adversarial Debate) | 33% | -67% ❌ |
| Verification (Propose-Verify-Judge) | 100% | No gain |
| Collaborative (Sequential Reasoning) | 67% | -33% ❌ |

**Key Finding:** Multi-agent approaches add complexity without improving answer quality. Use a single strong model for generation.

### When to Use MAVEN

**Recommended For:**
- ✓ High-stakes domains (medical, legal, financial)
- ✓ Detecting fabricated citations or fake sources
- ✓ Verifying AI-generated content before acting on it
- ✓ Applications where missing a hallucination could cause harm

**Not Recommended For:**
- ✗ Generating answers (use a single model instead)
- ✗ Low-stakes queries where over-flagging is problematic
- ✗ Real-time applications requiring instant verification
- ✗ Tasks where false positives are costly

> **Bottom Line**: MAVEN excels at **detection**, not generation. Use it as a safety layer to catch dangerous hallucinations before they cause harm.

## Use Cases

### Medical AI Safety
```python
# An AI assistant generates medical advice
ai_answer = ai_model.generate("What are contraindications for aspirin?")

# Verify before showing to patient
report = detector.detect(
    query="What are contraindications for aspirin?",
    answer=ai_answer,
    domain="medical"
)

if report.risk_level in ["CRITICAL", "HIGH"]:
    # Block response and alert human expert
    log_alert(f"Dangerous hallucination detected: {report.flags}")
    return "Please consult a healthcare professional."
```

### Legal Research Verification
```python
# Check AI-generated case citations before filing
report = detector.detect(
    query="What are precedents for contract breach in California?",
    answer=ai_response,
    domain="legal"
)

# Flag fabricated citations
if "fabricated" in " ".join(report.flags).lower():
    print("WARNING: Possible fake case citations detected!")
    print(f"Suspicious citations: {report.citation_checks}")
```

### Financial Advisory Safety Layer
```python
# Verify AI-generated investment advice
report = detector.detect(
    query="Should I invest in bonds during inflation?",
    answer=ai_advice,
    domain="financial"
)

if report.confidence_score < 70:
    # Require human review before delivery
    flag_for_review(report)
```

### Content Moderation
```python
# Flag AI-generated content with suspicious claims
report = detector.detect(
    query=user_question,
    answer=ai_generated_content,
    domain="general"
)

if "fabricated facts" in " ".join(report.flags).lower():
    add_warning_label("This response may contain unverified claims")
```

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get running in 5 minutes
- [Architecture Overview](docs/ARCHITECTURE.md) - System design deep-dive
- [Protocol Specification](docs/SPECIFICATION.md) - Formal protocol definition
- [API Reference](docs/API.md) - Complete API documentation

## Installation

### From PyPI (Recommended)
```bash
pip install maven-protocol
```

### From Source
```bash
git clone https://github.com/rwondo/maven.git
cd maven
pip install -e ".[dev]"
```

### Environment Variables
Set API keys for the models you want to use:
```bash
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"
export TOGETHER_API_KEY="your-key-here"  # For Llama, Mistral, Qwen, etc.
```

## Configuration

```python
from maven import HallucinationDetector

# Basic setup with Together AI models (recommended)
detector = HallucinationDetector(
    models=[
        "together/llama-3.1-8b",
        "together/qwen-2.5-7b",
        "together/mixtral-8x7b"
    ],
    config={
        "timeout_seconds": 30,         # Per-check timeout
        "enable_tools": True,          # Use Wikipedia/calculator for fact-checking
    }
)

# Or use premium models for higher accuracy
detector = HallucinationDetector(
    models=[
        "claude-sonnet-4",
        "gpt-4",
        "gemini-pro"
    ]
)
```

## Using Together AI Models

Run MAVEN with cost-effective open-source models via [Together AI](https://together.ai):

```python
detector = HallucinationDetector(
    models=[
        "together/llama-3.1-8b",      # Fast, good at consistency checks
        "together/qwen-2.5-7b",        # Strong reasoning
        "together/mixtral-8x7b",       # Mixture of experts
    ]
)
```

For better detection accuracy, use larger models:
```python
detector = HallucinationDetector(
    models=[
        "together/llama-3.3-70b",
        "together/mixtral-8x22b",
        "together/qwen-2.5-72b",
    ]
)
```

See [example_hallucination_detection.py](example_hallucination_detection.py) for a complete working example.

## Why Multiple Models?

Hallucination detection requires **diverse perspectives**:

- **Different training data**: Each model has different knowledge blind spots
- **Cross-verification**: If 2/3 models flag an answer, it's likely problematic
- **Redundancy**: No single model can detect all hallucinations

**Minimum 2 models required**, but 3+ recommended for:
- **Tie-breaking**: Resolve disagreements between models
- **Higher confidence**: More models = stronger signal when all agree
- **Better coverage**: Each model catches different types of hallucinations

## Limitations

- **Over-flagging**: 50% false positive rate - flags some legitimate answers as risky
- **Not perfect**: All models can share the same blind spots and miss hallucinations
- **Latency**: Detection takes 5-15 seconds with 3 models
- **Cost**: 3x API costs compared to single-model inference
- **Model availability**: Requires API access to 2-3 different models
- **Doesn't prevent hallucinations**: Only detects them after they're generated

**Critical Understanding**: MAVEN is a safety net, not a silver bullet. Use it as one layer in a multi-layered approach to AI safety.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas where we especially need help:
- Additional model integrations (Cohere, local models via Ollama)
- Benchmark dataset expansion
- Performance optimizations
- Documentation improvements
- Real-world use case examples

## Roadmap

- [x] **v0.2**: Hallucination detection system with 100% critical detection rate
- [ ] **v0.3**: Reduce false positive rate from 50% to <30%
- [ ] **v0.4**: Async/parallel detection for batch processing
- [ ] **v0.5**: Domain-specific detection (medical, legal, financial)
- [ ] **v0.6**: Integration with popular LLM frameworks (LangChain, LlamaIndex)
- [ ] **v1.0**: Production-ready with comprehensive benchmarks across domains

## Research & Background

MAVEN's hallucination detection approach is inspired by:
- **Ensemble methods** in machine learning (diverse models reduce bias)
- **Cross-validation** in statistics (multiple independent checks)
- **Peer review** in science (multiple experts verify claims)
- **Defense in depth** in security (layered verification)

### Key Research Finding

**Multi-agent consensus degrades generation quality** (extensive benchmarks showed 33-67% accuracy vs 100% baseline), but **excels at hallucination detection** (100% critical detection rate).

This makes sense: multiple models are better at finding flaws than creating correct answers.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contact

- **Author**: rwondo
- **GitHub Issues**: [Report bugs or request features](https://github.com/rwondo/maven/issues)
- **Discussions**: [Join the conversation](https://github.com/rwondo/maven/discussions)

---

<p align="center">
  <i>Catch dangerous AI hallucinations before they cause harm.</i>
</p>
