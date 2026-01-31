# MAVEN Test Suite

Comprehensive test suite for the MAVEN protocol implementation.

## Structure

```
tests/
├── __init__.py                 # Package marker
├── conftest.py                 # Pytest fixtures and configuration
├── test_orchestrator.py        # Tests for ConsensusOrchestrator
├── test_consensus.py           # Tests for consensus detection
└── test_roles.py               # Tests for role prompts
```

## Running Tests

### All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=maven --cov-report=html
```

### Specific Test Files

```bash
# Test orchestrator only
pytest tests/test_orchestrator.py -v

# Test consensus logic only
pytest tests/test_consensus.py -v

# Test role prompts only
pytest tests/test_roles.py -v
```

### Specific Test Classes or Functions

```bash
# Run specific test class
pytest tests/test_orchestrator.py::TestOrchestratorInitialization -v

# Run specific test function
pytest tests/test_orchestrator.py::TestOrchestratorInitialization::test_init_with_valid_models -v
```

### Test Markers

```bash
# Skip slow tests
pytest tests/ -v -m "not slow"

# Run only integration tests
pytest tests/ -v -m "integration"
```

## Test Coverage

Current test coverage targets:

- **Orchestrator**: >85% coverage
- **Consensus**: >90% coverage
- **Roles**: >95% coverage
- **Models**: >80% coverage
- **Utils**: >85% coverage

View coverage report:

```bash
pytest tests/ --cov=maven --cov-report=html
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html # Windows
```

## Writing Tests

### Test Naming Convention

- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<function>_<scenario>`

Example:

```python
class TestConsensusOrchestrator:
    """Tests for ConsensusOrchestrator class."""

    def test_verify_returns_consensus_result(self):
        """Verify returns a ConsensusResult object."""
        # Test implementation
```

### Using Fixtures

Fixtures are defined in `conftest.py` and available to all tests:

```python
def test_with_mock_models(mock_models):
    """Test using mock models fixture."""
    # mock_models is automatically injected
    assert len(mock_models) == 3
```

Available fixtures:

- `mock_model_ids` - List of mock model identifiers
- `mock_models` - Configured mock model instances
- `disagreeing_mock_models` - Mock models that disagree
- `sample_responses` - Sample ModelResponse objects
- `sample_trace` - Sample trace steps
- `sample_consensus_result` - Sample ConsensusResult
- `mock_orchestrator` - Orchestrator with mocked models
- `default_config` - Default configuration dict
- `strict_config` - Strict configuration dict
- `sample_queries` - List of test queries

### Mock vs Integration Tests

**Unit Tests (Mock):**
- Fast, no API calls
- Use mock models from fixtures
- Test logic and structure
- Run by default

```python
def test_orchestrator_init(mock_model_ids):
    """Unit test with mocked models."""
    orchestrator = ConsensusOrchestrator(models=mock_model_ids)
    assert len(orchestrator.model_ids) == 3
```

**Integration Tests (Real APIs):**
- Slower, requires API keys
- Use real model APIs
- Test end-to-end functionality
- Mark with `@pytest.mark.integration`

```python
@pytest.mark.integration
def test_real_verification():
    """Integration test with real APIs."""
    orchestrator = ConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
    )
    result = orchestrator.verify("Test query")
    assert result.consensus is not None
```

### Test Organization

Organize tests by functionality:

```python
class TestOrchestratorInitialization:
    """Tests for initialization."""
    def test_init_with_valid_models(self): ...
    def test_init_fails_with_too_few_models(self): ...

class TestRoleAssignment:
    """Tests for role assignment."""
    def test_assign_roles_returns_three_roles(self): ...
    def test_role_rotation_changes_roles(self): ...

class TestVerification:
    """Tests for verification process."""
    def test_verify_returns_consensus_result(self): ...
    def test_verify_rejects_empty_query(self): ...
```

## Continuous Integration

Tests run automatically on GitHub Actions:

- Every push to `main` or `develop`
- Every pull request
- Python versions: 3.9, 3.10, 3.11, 3.12

See `.github/workflows/ci.yml` for configuration.

## Debugging Tests

### Run with Extra Output

```bash
# Show print statements
pytest tests/ -v -s

# Show locals on failure
pytest tests/ -v -l

# Stop at first failure
pytest tests/ -v -x

# Drop into debugger on failure
pytest tests/ -v --pdb
```

### Run Specific Failing Test

```bash
# Get test name from failure output
pytest tests/test_orchestrator.py::TestVerification::test_verify_returns_consensus_result -v
```

### Check Test Discovery

```bash
# List all tests without running
pytest --collect-only

# Show test execution order
pytest --setup-show
```

## Code Coverage Goals

Maintain high coverage for reliability:

- Overall: **>80%**
- Core modules: **>85%**
- Critical paths: **>90%**

Generate coverage report:

```bash
pytest tests/ --cov=maven --cov-report=term-missing
```

## Test Data

Test data is located in:

- `tests/conftest.py` - Shared fixtures
- `benchmarks/datasets/` - Benchmark queries
- Tests themselves - Inline test data

## Adding New Tests

When adding new functionality:

1. Write tests first (TDD)
2. Add appropriate fixtures to `conftest.py`
3. Use descriptive test names
4. Add docstrings explaining what is tested
5. Group related tests in classes
6. Ensure tests pass: `pytest tests/ -v`
7. Check coverage: `pytest tests/ --cov=maven`

## Questions?

- Check pytest documentation: https://docs.pytest.org
- See existing tests for examples
- Ask in GitHub Discussions
