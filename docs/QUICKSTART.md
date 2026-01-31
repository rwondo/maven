# Quick Start Guide

Get MAVEN running in 5 minutes.

## Installation

```bash
pip install maven-protocol
```

Or install from source:

```bash
git clone https://github.com/arberferra/maven.git
cd maven
pip install -e .
```

## Set Up API Keys

MAVEN needs API keys for the models you want to use:

```bash
# For Claude, GPT, Gemini
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"

# For Together AI (Llama, Mistral, Qwen, etc.)
export TOGETHER_API_KEY="your-together-key"
```

## Basic Example

```python
from maven import ConsensusOrchestrator

# Create orchestrator with three models
orchestrator = ConsensusOrchestrator(
    models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
)

# Verify a factual claim
result = orchestrator.verify(
    query="What is the capital of Australia?"
)

# Check the result
print(f"Answer: {result.consensus}")
print(f"Confidence: {result.confidence}%")
print(f"Iterations needed: {result.iterations}")
```

## Understanding Results

The `verify()` method returns a `ConsensusResult` object:

```python
result.consensus      # The agreed-upon answer
result.confidence     # Confidence score (0-100)
result.iterations     # Number of rounds needed
result.trace          # Full verification audit trail
result.dissent        # Any dissenting opinions (if 2/3 consensus)
```

## Viewing the Trace

The trace shows the complete verification process:

```python
for step in result.trace:
    print(f"[{step.role}] {step.model}: {step.summary}")
```

## Configuration Options

```python
orchestrator = ConsensusOrchestrator(
    models=["claude-sonnet-4", "gpt-4", "gemini-pro"],
    config={
        "max_iterations": 5,
        "consensus_threshold": 0.8,
        "timeout_seconds": 60,
    }
)
```

## Using Together AI Models

Together AI provides access to open-source models like Llama, Mistral, and Qwen:

```python
orchestrator = ConsensusOrchestrator(
    models=[
        "together/llama-3.3-70b",
        "together/mixtral-8x22b",
        "together/qwen-2.5-72b",
    ]
)

result = orchestrator.verify("Your question here")
```

Available aliases:
- `together/llama-3.3-70b` - Llama 3.3 70B
- `together/llama-3.1-405b` - Llama 3.1 405B
- `together/mixtral-8x22b` - Mixtral 8x22B
- `together/qwen-2.5-72b` - Qwen 2.5 72B
- `together/deepseek-r1-70b` - DeepSeek R1 70B

You can also use full model paths:
```python
models=["meta-llama/Llama-3.3-70B-Instruct-Turbo", ...]
```

## Next Steps

- See [examples/](../examples/) for more use cases
- See [examples/together_ai_example.py](../examples/together_ai_example.py) for Together AI usage
- Read the [API Reference](API.md) for full documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
