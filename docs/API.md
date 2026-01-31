# API Reference

Complete API documentation for MAVEN.

## ConsensusOrchestrator

The main class for running multi-model verification.

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
