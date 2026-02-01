# Contributing to MAVEN

Thank you for your interest in contributing to MAVEN! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Commit Message Conventions](#commit-message-conventions)
- [Pull Request Process](#pull-request-process)
- [Areas Needing Help](#areas-needing-help)
- [Questions?](#questions)

## Getting Started

1. **Fork the repository** on GitHub

2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/maven.git
   cd maven
   ```

3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/rwondo/maven.git
   ```

4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip or uv for package management
- Git

### Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up environment variables** (for running tests with real models):
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   export OPENAI_API_KEY="your-key"
   export GOOGLE_API_KEY="your-key"
   ```

4. **Verify installation**:
   ```bash
   python -c "import maven; print(maven.__version__)"
   pytest tests/ -v
   ```

## Code Style Guidelines

We follow strict code style guidelines to maintain consistency:

### Python Style

- **PEP 8**: Follow PEP 8 style guide
- **Black**: Use Black for code formatting (line length: 88)
- **Ruff**: Use Ruff for linting
- **Type Hints**: All functions must have type annotations

### Formatting Commands

```bash
# Format code
black src/ tests/ examples/

# Lint code
ruff check src/ tests/ examples/

# Type check
mypy src/
```

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def verify(self, query: str, max_iterations: int = 5) -> ConsensusResult:
    """Run verification protocol on a query.

    Coordinates multiple models in adversarial roles to achieve
    consensus through iterative verification rounds.

    Args:
        query: The question or claim to verify.
        max_iterations: Maximum number of consensus rounds. Defaults to 5.

    Returns:
        ConsensusResult containing the consensus answer, confidence score,
        iteration count, and complete verification trace.

    Raises:
        ValueError: If query is empty or models are not configured.
        TimeoutError: If verification exceeds configured timeout.

    Example:
        >>> result = orchestrator.verify("What is the speed of light?")
        >>> print(result.consensus)
        "299,792,458 meters per second"
    """
```

### Import Organization

Organize imports in this order, separated by blank lines:

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
import logging
from typing import Dict, List, Optional

import anthropic
from pydantic import BaseModel

from maven.roles import RolePrompts
from maven.utils import generate_trace_id
```

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=maven --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py -v

# Run tests matching a pattern
pytest tests/ -v -k "test_consensus"
```

### Writing Tests

- **Coverage target**: Aim for >80% code coverage
- **Test file naming**: `test_<module>.py`
- **Test function naming**: `test_<function>_<scenario>`
- **Use fixtures**: Define reusable test fixtures in `conftest.py`

Example test:

```python
import pytest
from maven import ConsensusOrchestrator
from maven.consensus import ConsensusResult

class TestOrchestrator:
    """Tests for ConsensusOrchestrator class."""

    def test_verify_returns_consensus_result(self, mock_models):
        """Verify returns a properly structured ConsensusResult."""
        orchestrator = ConsensusOrchestrator(models=mock_models)
        result = orchestrator.verify("Test query")

        assert isinstance(result, ConsensusResult)
        assert result.consensus is not None
        assert 0 <= result.confidence <= 100

    def test_verify_respects_max_iterations(self, mock_models):
        """Verify stops after max_iterations rounds."""
        orchestrator = ConsensusOrchestrator(models=mock_models)
        result = orchestrator.verify("Test query", max_iterations=2)

        assert result.iterations <= 2
```

### Mock Models

For unit tests, use mock models instead of real API calls:

```python
@pytest.fixture
def mock_models():
    """Provide mock model configurations for testing."""
    return ["mock-model-1", "mock-model-2", "mock-model-3"]
```

## Commit Message Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

### Examples

```
feat(orchestrator): add support for role rotation between rounds

fix(consensus): handle edge case when all models timeout

docs(readme): add benchmark results table

test(roles): add tests for Skeptic prompt generation

refactor(models): extract common API client logic
```

## Pull Request Process

1. **Ensure your branch is up to date**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks locally**:
   ```bash
   black src/ tests/ examples/
   ruff check src/ tests/ examples/
   mypy src/
   pytest tests/ -v
   ```

3. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub with:
   - Clear title following commit conventions
   - Description of changes
   - Link to related issue (if applicable)
   - Screenshots/examples (if applicable)

5. **Address review feedback** by pushing additional commits

6. **Squash and merge** once approved

### PR Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New code has test coverage
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (for significant changes)

## Areas Needing Help

We especially welcome contributions in these areas:

### Model Integrations
- Llama (via Ollama or llama.cpp)
- Mistral
- Cohere
- Local model support

### Benchmarks
- Expand benchmark dataset
- Add domain-specific benchmarks
- Improve benchmark methodology

### Performance
- Async/parallel model calls
- Response streaming
- Caching layer

### Documentation
- Tutorials and guides
- API examples
- Translations

### Testing
- Edge case coverage
- Integration tests
- Performance tests

## Questions?

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Email**: arberferra@example.com

---

Thank you for contributing to MAVEN! Your efforts help make AI systems more reliable and trustworthy.
