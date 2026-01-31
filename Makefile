# Makefile for MAVEN development
# Works on Linux/Mac. For Windows, use make.bat or run commands directly

.PHONY: help install test lint format clean build publish docs

help:  ## Show this help message
	@echo "MAVEN Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package in development mode
	pip install -e ".[dev]"

test:  ## Run all tests
	pytest tests/ -v

test-cov:  ## Run tests with coverage
	pytest tests/ -v --cov=maven --cov-report=html --cov-report=term

test-fast:  ## Run tests without slow tests
	pytest tests/ -v -m "not slow"

lint:  ## Run linters (ruff + mypy)
	ruff check src/ tests/ examples/
	mypy src/

lint-fix:  ## Run linters and auto-fix issues
	ruff check --fix src/ tests/ examples/

format:  ## Format code with black
	black src/ tests/ examples/

format-check:  ## Check code formatting
	black --check src/ tests/ examples/

check:  ## Run all checks (format, lint, test)
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

publish-test:  ## Upload to TestPyPI
	twine upload --repository testpypi dist/*

publish:  ## Upload to PyPI
	twine upload dist/*

docs:  ## Open documentation in browser
	@echo "Opening documentation..."
	@python -m webbrowser docs/QUICKSTART.md

pre-commit:  ## Install pre-commit hooks
	pre-commit install
	pre-commit run --all-files

test-together:  ## Test Together AI integration
	python test_together.py

example-basic:  ## Run basic example
	python examples/basic_consensus.py

example-together:  ## Run Together AI example
	python examples/together_ai_example.py

example-security:  ## Run code security example
	python examples/code_security_review.py

.DEFAULT_GOAL := help
