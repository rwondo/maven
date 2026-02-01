# API Reference

Complete API documentation for MAVEN.

## HallucinationDetector

**PRIMARY API** - The main class for detecting hallucinations in AI-generated content.

### Constructor

```python
HallucinationDetector(
    models: List[str],
    config: Optional[Dict[str, Any]] = None
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `models` | `List[str]` | List of model identifiers (minimum 2 required) |
| `config` | `Dict` | Optional configuration dictionary |

**Example:**

```python
from maven import HallucinationDetector

detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b", "together/mixtral-8x7b"]
)
```

### detect()

```python
def detect(
    self,
    query: str,
    answer: str,
    domain: Optional[str] = None
) -> HallucinationReport
```

Detect potential hallucinations in an AI-generated answer.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | The original question that was asked |
| `answer` | `str` | required | The AI-generated answer to verify |
| `domain` | `str` | None | Domain context (e.g., "medical", "legal", "financial") |

**Returns:** `HallucinationReport`

**Example:**

```python
report = detector.detect(
    query="What are contraindications for aspirin?",
    answer="According to the 2023 Johnson Study published in NEJM...",
    domain="medical"
)

if report.risk_level in ["CRITICAL", "HIGH"]:
    print(f"WARNING: {report.flags}")
```

---

## HallucinationReport

Container for hallucination detection results.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `risk_level` | `str` | Overall risk: "LOW", "MEDIUM", "HIGH", or "CRITICAL" |
| `confidence_score` | `float` | Confidence the answer is accurate (0-100) |
| `flags` | `List[str]` | Specific issues detected |
| `consistency_score` | `float` | How well models agree (0-100) |
| `fact_checks` | `List[Dict]` | Results from fact verification |
| `citation_checks` | `List[Dict]` | Results from citation verification |
| `logic_checks` | `List[Dict]` | Results from logical consistency checks |
| `model_responses` | `List[str]` | What each model said |
| `disagreements` | `List[str]` | Where models disagreed |
| `trace` | `List[TraceStep]` | Complete audit trail |
| `metadata` | `Dict` | Additional result metadata |

### Methods

#### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

Convert report to dictionary format for serialization.

---

## ConsensusOrchestrator (Experimental)

**NOT RECOMMENDED FOR PRODUCTION** - Multi-agent consensus for answer generation. Benchmarks showed this degrades accuracy (33-67% vs 100% single-model baseline).

Use `HallucinationDetector` instead for production applications.

### Constructor

```python
ConsensusOrchestrator(
    models: List[str],
    config: Optional[Dict[str, Any]] = None
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `models` | `List[str]` | List of model identifiers (minimum 3) |
| `config` | `Dict` | Optional configuration dictionary |

**Supported Models:**

- `claude-sonnet-4`, `claude-opus-4` (Anthropic)
- `gpt-4`, `gpt-4-turbo` (OpenAI)
- `gemini-pro`, `gemini-ultra` (Google)
- Together AI models (see below)

**Together AI Models:**

Use the `together/` prefix or full model paths:

| Alias | Full Path |
|-------|-----------|
| `together/llama-3.3-70b` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| `together/llama-3.1-405b` | `meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo` |
| `together/llama-3.1-70b` | `meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo` |
| `together/llama-3.1-8b` | `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` |
| `together/mixtral-8x22b` | `mistralai/Mixtral-8x22B-Instruct-v0.1` |
| `together/mixtral-8x7b` | `mistralai/Mixtral-8x7B-Instruct-v0.1` |
| `together/qwen-2.5-72b` | `Qwen/Qwen2.5-72B-Instruct-Turbo` |
| `together/qwen-2.5-7b` | `Qwen/Qwen2.5-7B-Instruct-Turbo` |
| `together/deepseek-r1-70b` | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` |

You can also use full model paths directly (e.g., `meta-llama/Llama-3.3-70B-Instruct-Turbo`)

### verify()

```python
def verify(
    self,
    query: str,
    max_iterations: int = 5,
    context: Optional[Dict[str, Any]] = None
) -> ConsensusResult
```

Run the verification protocol on a query.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | The question or claim to verify |
| `max_iterations` | `int` | 5 | Maximum consensus rounds |
| `context` | `Dict` | None | Additional context for domain-specific verification |

**Returns:** `ConsensusResult`

**Raises:**
- `ValueError`: If query is empty or models not configured
- `TimeoutError`: If verification exceeds timeout
- `ConsensusError`: If consensus cannot be reached

---

## ConsensusResult

Container for verification results.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `consensus` | `str` | The agreed-upon answer |
| `confidence` | `float` | Confidence score (0-100) |
| `iterations` | `int` | Number of rounds completed |
| `trace` | `List[TraceStep]` | Complete audit trail |
| `dissent` | `Optional[str]` | Dissenting opinion if 2/3 consensus |
| `metadata` | `Dict` | Additional result metadata |

### Confidence Calculation

The `confidence` score (0-100) is calculated using a **multi-strategy weighted similarity algorithm** that analyzes model agreement:

**Strategy Weights:**
- **60% Structured Answer Extraction**: Extracts core answers from `ANSWER:`, `PROPOSED CONSENSUS:` markers
- **30% Numerical Value Comparison**: Identifies and compares numbers in responses (for arithmetic/quantitative queries)
- **10% Semantic Text Similarity**: Analyzes word overlap with stopword filtering

**How It Works:**

1. **Extract structured answers** from each model's response
2. **Compare numerical values** if present (e.g., "4" matches in "2+2=4")
3. **Calculate semantic similarity** between remaining text
4. **Apply weighted scoring** based on which strategies produced results
5. **Boost confidence** for exact numerical matches

**Examples:**

```python
# Simple arithmetic: High confidence from numerical agreement
Query: "What is 2 + 2?"
Model 1: "ANSWER: 4"
Model 2: "ANSWER: The answer is 4"
Model 3: "ANSWER: 2 + 2 = 4"
# Confidence: ~68-75% (all agree on "4")

# Factual agreement: Good confidence from structured answers
Query: "What is the capital of France?"
Model 1: "ANSWER: Paris"
Model 2: "ANSWER: The capital is Paris"
Model 3: "ANSWER: Paris, France"
# Confidence: ~70-85% (structured answers align)

# Verbose vs concise: Reasonable confidence despite different wording
Model 1: "ANSWER: 4.5 billion years"
Model 2: "ANSWER: Earth is approximately 4.5 billion years old, based on radiometric dating"
# Confidence: ~60-70% (numbers match, structured answers extracted)
```

**Performance Improvements:**

Compared to basic word-overlap similarity:
- Simple arithmetic: **20% → 68%** (+240% improvement)
- Structured answers: **44% → 75%** (+70% improvement)
- Verbose responses: **19% → 60%** (+216% improvement)

---

## TraceStep

Individual step in the verification trace.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `iteration` | `int` | Round number |
| `role` | `str` | Role (Architect/Skeptic/Mediator) |
| `model` | `str` | Model identifier |
| `content` | `str` | Full response content |
| `summary` | `str` | Brief summary |
| `timestamp` | `datetime` | When step occurred |

---

## Configuration Options

```python
config = {
    "max_iterations": 5,           # Max consensus rounds
    "consensus_threshold": 0.8,    # Required agreement level
    "timeout_seconds": 60,         # Per-iteration timeout
    "enable_role_rotation": True,  # Rotate roles between rounds
    "trace_verbosity": "full",     # "minimal", "standard", "full"
    "retry_on_error": True,        # Retry failed API calls
    "max_retries": 3,              # Maximum retry attempts
}
```

---

## Exceptions

### ConsensusError

Raised when consensus cannot be reached after max iterations.

```python
from maven.exceptions import ConsensusError

try:
    result = orchestrator.verify(query)
except ConsensusError as e:
    print(f"Failed to reach consensus: {e}")
    print(f"Best answer: {e.best_answer}")
    print(f"Disagreement points: {e.disagreements}")
```

### ModelError

Raised when a model fails to respond.

```python
from maven.exceptions import ModelError

try:
    result = orchestrator.verify(query)
except ModelError as e:
    print(f"Model {e.model} failed: {e.message}")
```
