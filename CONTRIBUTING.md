# Contributing

MAVEN is a small personal prototype, but issues and pull requests are welcome. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Setup

```bash
git clone https://github.com/rwondo/maven.git
cd maven
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install             # optional: runs ruff and mypy before each commit
```

## Checks

CI runs these on every push and pull request. Run them locally before opening a pull request:

```bash
pytest
ruff check src tests scripts
ruff format --check src tests scripts
mypy src scripts
```

CI installs the exact versions in `requirements-dev.lock`. After changing dependencies in `pyproject.toml`, regenerate it with:

```bash
uv pip compile pyproject.toml --extra dev --universal --python-version 3.10 -o requirements-dev.lock
```

## Guidelines

- Tests must not call real model APIs. Use `MockModel` / `AsyncMockModel`, or monkeypatch `create_model`.
- Keep the README honest: any claim about accuracy must come from a run of `scripts/evaluate_truthfulqa.py` whose JSON output is committed under `results/`.
- Write commit messages as a short imperative summary line, then a body explaining why.

Bugs and ideas go in [GitHub issues](https://github.com/rwondo/maven/issues).
