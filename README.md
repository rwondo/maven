# MAVEN - Multi-Agent Verification & Evaluation Network

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/arberferra/maven?style=social)](https://github.com/arberferra/maven)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Reduce AI hallucinations through multi-model adversarial consensus.**

---

## The Problem

AI models hallucinate. They confidently state incorrect facts, invent citations, and produce plausible-sounding but wrong outputs. In high-stakes domains—medical diagnosis, legal analysis, financial decisions, code security—these hallucinations can be catastrophic.

Single-model approaches to reducing hallucinations (better prompting, retrieval augmentation, fine-tuning) help, but they can't catch errors the model is fundamentally blind to.

## The Solution

**MAVEN** orchestrates multiple AI models in adversarial roles to verify outputs through peer-to-peer consensus. Instead of trusting one model's answer, MAVEN forces models to prove their logic to each other.

Three models participate with randomized roles:
- **Architect**: Proposes an initial well-reasoned solution
- **Skeptic**: Challenges assumptions and identifies logical flaws
- **Mediator**: Synthesizes discussion and builds consensus

The protocol continues until **3/3 consensus** is reached, or **2/3 agreement** with documented dissent.

Every verification produces a complete **Logic Trace**—a human-readable audit trail showing exactly how consensus was (or wasn't) achieved.

## Quick Start

```bash
pip install maven-protocol
```

```python
from maven import ConsensusOrchestrator

# Initialize with three models
orchestrator = ConsensusOrchestrator(
    models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
)

# Verify a claim
result = orchestrator.verify("What causes the seasons on Earth?")

print(f"Answer: {result.consensus}")
print(f"Confidence: {result.confidence}%")
```

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │         ConsensusOrchestrator           │
                    │  (Role Assignment & Protocol Control)   │
                    └────────────────┬────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
           ▼                         ▼                         ▼
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │  Model A    │          │  Model B    │          │  Model C    │
    │ (Architect) │◄────────►│  (Skeptic)  │◄────────►│ (Mediator)  │
    └─────────────┘          └─────────────┘          └─────────────┘
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────────┐
                    │          ConsensusDetector              │
                    │   (Agreement Analysis & Exit Criteria)  │
                    └────────────────┬────────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────────────┐
                    │             Logic Trace                 │
                    │     (Complete Audit Trail Output)       │
                    └─────────────────────────────────────────┘
```

### Verification Flow

1. **Role Assignment**: Models are randomly assigned Architect/Skeptic/Mediator roles
2. **Proposal**: Architect provides initial reasoned response
3. **Challenge**: Skeptic identifies weaknesses, requests evidence
4. **Synthesis**: Mediator integrates feedback, proposes consensus
5. **Check**: ConsensusDetector evaluates agreement level
6. **Iterate**: If no consensus, roles may rotate for next round
7. **Output**: Final answer with confidence score and complete trace

## Benchmarks

| Metric | Single Model | MAVEN (3 Models) | Improvement |
|--------|-------------|------------------|-------------|
| Factual Accuracy | 78.3% | 94.7% | +16.4% |
| Hallucination Rate | 12.1% | 2.3% | -81% |
| Confidence Calibration | 0.67 | 0.91 | +36% |
| Avg. Response Time | 1.2s | 8.4s | +600% |

*Benchmarks run on 1,000 factual queries across geography, science, history, and current events. See [benchmarks/](benchmarks/) for methodology and full results.*

> **Trade-off**: MAVEN significantly improves accuracy at the cost of latency and API calls. Use it when correctness matters more than speed.

## Use Cases

### Code Security Review
```python
result = orchestrator.verify(
    query="Review this code for security vulnerabilities:\n" + code,
    context={"domain": "security", "severity_threshold": "medium"}
)
```

### Medical Information Synthesis
```python
result = orchestrator.verify(
    query="What are the contraindications for combining aspirin with warfarin?",
    context={"domain": "medical", "require_citations": True}
)
```

### Legal Document Analysis
```python
result = orchestrator.verify(
    query="Does this contract clause comply with GDPR Article 17?",
    context={"domain": "legal", "jurisdiction": "EU"}
)
```

### Fact-Checking
```python
result = orchestrator.verify(
    query="Is it true that the Great Wall of China is visible from space?",
    context={"domain": "factual", "require_sources": True}
)
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
git clone https://github.com/arberferra/maven.git
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
orchestrator = ConsensusOrchestrator(
    models=["claude-sonnet-4", "gpt-4", "gemini-pro"],
    config={
        "max_iterations": 5,           # Maximum consensus rounds
        "consensus_threshold": 0.8,    # Required agreement level
        "timeout_seconds": 60,         # Per-iteration timeout
        "enable_role_rotation": True,  # Rotate roles between rounds
        "trace_verbosity": "full",     # "minimal", "standard", "full"
    }
)
```

## Using Together AI Models

Run MAVEN with open-source models via [Together AI](https://together.ai):

```python
orchestrator = ConsensusOrchestrator(
    models=[
        "together/llama-3.3-70b",
        "together/mixtral-8x22b",
        "together/qwen-2.5-72b",
    ]
)
```

Available aliases: `llama-3.3-70b`, `llama-3.1-405b`, `mixtral-8x22b`, `qwen-2.5-72b`, `deepseek-r1-70b`, and more. See [examples/together_ai_example.py](examples/together_ai_example.py).

## Why Three Models?

Two models create deadlocks. Four models add cost without proportional benefit. Three models provide:

- **Tie-breaking capability**: Mediator resolves Architect-Skeptic disputes
- **Diverse perspectives**: Different training data catches different blind spots
- **Efficient consensus**: O(n) communication, not O(n²)
- **Cost-effectiveness**: Balances accuracy gains against API costs

## Limitations

- **Latency**: 5-10x slower than single-model responses
- **Cost**: 3x+ API costs (more with multiple iterations)
- **Not a guarantee**: Consensus doesn't mean correctness—all models can share blind spots
- **Model availability**: Requires API access to multiple providers
- **Context limits**: Very long inputs may exceed model context windows

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas where we especially need help:
- Additional model integrations (Cohere, local models via Ollama)
- Benchmark dataset expansion
- Performance optimizations
- Documentation improvements
- Real-world use case examples

## Roadmap

- [ ] **v0.2**: Streaming support for real-time trace output
- [ ] **v0.3**: Local model support (Ollama, llama.cpp)
- [ ] **v0.4**: Async/parallel verification for batch processing
- [ ] **v0.5**: Web UI for interactive verification
- [ ] **v1.0**: Production-ready with comprehensive test coverage

## Research & Background

MAVEN is inspired by:
- Constitutional AI and self-critique mechanisms
- Ensemble methods in machine learning
- Adversarial collaboration in science
- Peer review processes

For the theoretical foundation, see our [Protocol Specification](docs/SPECIFICATION.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contact

- **Author**: Arber Ferra
- **GitHub Issues**: [Report bugs or request features](https://github.com/arberferra/maven/issues)
- **Discussions**: [Join the conversation](https://github.com/arberferra/maven/discussions)

---

<p align="center">
  <i>Built with the belief that AI systems should be verifiable, not just capable.</i>
</p>
