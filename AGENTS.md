# AGENTS.md - AI Coding Assistant Instructions

This file provides context for AI coding assistants working on the MAVEN project.

## Project Overview

MAVEN (Multi-Agent Verification & Evaluation Network) is a Python library that orchestrates multiple AI models to verify outputs through consensus. The goal is to reduce hallucinations by having models check each other's work.

## Repository Structure

```
maven/
├── src/maven/          # Core library code
├── tests/              # Test suite
├── examples/           # Usage examples
├── docs/               # Documentation
└── benchmarks/         # Performance benchmarks
```

## Build and Test Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=maven

# Format code
black src/ tests/ examples/

# Lint code
ruff check src/ tests/ examples/

# Type check
mypy src/
```

## Code Style Guidelines

- Follow PEP 8
- Use type hints on all functions
- Use Google-style docstrings
- Maximum line length: 100 characters
- Format with Black, lint with Ruff

## Architecture Overview

Key components:
- `ConsensusOrchestrator`: Main class that coordinates verification
- `ModelInterface`: Abstract base class for model integrations
- `RolePrompts`: System prompts for each role (Architect, Skeptic, Mediator)
- `ConsensusDetector`: Determines when agreement is reached

## Testing Instructions

- Unit tests use mock models (no API calls)
- Integration tests require API keys in environment
- Aim for >80% code coverage
- Test edge cases: timeouts, disagreements, empty responses

## Common Development Tasks

### Adding a new model integration
1. Create new class in `src/maven/models.py`
2. Inherit from `ModelInterface`
3. Implement `generate()` method
4. Add tests in `tests/test_models.py`

### Modifying role prompts
1. Edit `src/maven/roles.py`
2. Update tests in `tests/test_roles.py`
3. Run benchmark comparison to verify performance
