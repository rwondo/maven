# Professional Setup Guide for MAVEN

Complete guide to set up MAVEN for development, testing, and GitHub deployment.

## Table of Contents

- [Initial Git Setup](#initial-git-setup)
- [GitHub Repository Setup](#github-repository-setup)
- [Development Environment](#development-environment)
- [Testing Setup](#testing-setup)
- [CI/CD Configuration](#cicd-configuration)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Publishing to PyPI](#publishing-to-pypi)

---

## Initial Git Setup

### 1. Initialize Git Repository

```bash
cd c:\Users\39392\OneDrive\Desktop\maven

# Initialize git (if not already done)
git init

# Add all files
git add .

# Make initial commit
git commit -m "feat: initial commit - MAVEN protocol implementation

- Core orchestration with adversarial consensus
- Support for Claude, GPT, Gemini, Together AI
- Async orchestrator for batch processing
- Complete test suite and documentation
- CLI interface
- Benchmark dataset with 99 queries"
```

### 2. Configure Git User

```bash
# Set your name and email
git config user.name "Arber Ferra"
git config user.email "your.email@example.com"

# Verify
git config --list
```

---

## GitHub Repository Setup

### 1. Create GitHub Repository

**Option A: Via GitHub CLI (Recommended)**

```bash
# Install GitHub CLI if not already installed
# On Windows: winget install --id GitHub.cli

# Login to GitHub
gh auth login

# Create repository
gh repo create maven --public --description "Multi-Agent Verification & Evaluation Network - Reduce AI hallucinations through multi-model consensus" --source=. --remote=origin

# Push code
git push -u origin main
```

**Option B: Via GitHub Web Interface**

1. Go to https://github.com/new
2. Repository name: `maven`
3. Description: "Multi-Agent Verification & Evaluation Network - Reduce AI hallucinations through multi-model consensus"
4. Choose: Public
5. **DO NOT** initialize with README (you already have one)
6. Click "Create repository"

Then connect your local repo:

```bash
git remote add origin https://github.com/YOUR_USERNAME/maven.git
git branch -M main
git push -u origin main
```

### 2. Configure Repository Settings

On GitHub, go to your repository settings:

**General Settings:**
- Enable "Discussions" for community questions
- Add topics: `ai`, `llm`, `verification`, `consensus`, `python`, `hallucination`

**Branch Protection (Settings → Branches):**
- Add rule for `main` branch
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass (CI tests)
- ✅ Require branches to be up to date

**Secrets (Settings → Secrets and variables → Actions):**

Add these secrets for GitHub Actions:

```
ANTHROPIC_API_KEY  (for integration tests - optional)
OPENAI_API_KEY     (for integration tests - optional)
GOOGLE_API_KEY     (for integration tests - optional)
TOGETHER_API_KEY   (for integration tests - optional)
PYPI_API_TOKEN     (for publishing - add later)
```

**About Section:**
- Add website: https://github.com/YOUR_USERNAME/maven
- Add topics/tags
- Add description

---

## Development Environment

### 1. Python Environment Setup

```bash
# Ensure Python 3.9+ is installed
python --version

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Windows CMD:
.venv\Scripts\activate.bat

# Linux/Mac:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import maven; print(maven.__version__)"
```

### 3. Set Up API Keys

Create a `.env` file in the project root (already in `.gitignore`):

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
TOGETHER_API_KEY=...
```

Load environment variables:

```bash
# Windows PowerShell:
Get-Content .env | ForEach-Object {
    $name, $value = $_.split('=')
    Set-Content env:\$name $value
}

# Linux/Mac:
export $(cat .env | xargs)
```

**Or use python-dotenv:**

```bash
pip install python-dotenv
```

```python
# In your code
from dotenv import load_dotenv
load_dotenv()
```

---

## Testing Setup

### 1. Run All Tests

```bash
# Run tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=maven --cov-report=html --cov-report=term

# View coverage report
# Windows:
start htmlcov/index.html

# Linux/Mac:
open htmlcov/index.html
```

### 2. Run Specific Test Categories

```bash
# Run only unit tests (no API calls)
pytest tests/test_orchestrator.py tests/test_consensus.py tests/test_roles.py -v

# Run with markers
pytest -m "not slow" -v

# Run specific test
pytest tests/test_orchestrator.py::TestOrchestratorInitialization::test_init_with_valid_models -v
```

### 3. Test Individual Examples

```bash
# Test basic consensus example
python examples/basic_consensus.py

# Test Together AI integration
python examples/together_ai_example.py

# Test code security review
python examples/code_security_review.py
```

### 4. Code Quality Checks

```bash
# Format code
black src/ tests/ examples/

# Check formatting (CI mode)
black --check src/ tests/ examples/

# Lint code
ruff check src/ tests/ examples/

# Fix linting issues automatically
ruff check --fix src/ tests/ examples/

# Type checking
mypy src/
```

---

## CI/CD Configuration

### 1. Verify GitHub Actions

Your CI is already configured in `.github/workflows/ci.yml`. Verify it works:

```bash
# Push code to trigger CI
git add .
git commit -m "test: trigger CI pipeline"
git push
```

Go to GitHub → Actions tab to see the build status.

### 2. Add Status Badges to README

Update your README.md with build badges:

```markdown
[![CI](https://github.com/YOUR_USERNAME/maven/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/maven/actions)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/maven/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/maven)
```

### 3. Set Up Codecov (Optional)

1. Go to https://codecov.io
2. Sign in with GitHub
3. Add your `maven` repository
4. Copy the token
5. Add `CODECOV_TOKEN` to GitHub Secrets

---

## Pre-commit Hooks

### 1. Install Pre-commit

```bash
pip install pre-commit
```

### 2. Create Pre-commit Config

```bash
# This file: .pre-commit-config.yaml
```

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
```

### 3. Install Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files (first time)
pre-commit run --all-files

# Test it
git add .
git commit -m "test: verify pre-commit hooks"
```

---

## Publishing to PyPI

### 1. Prepare for Publishing

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*
```

### 2. Test on TestPyPI First

```bash
# Create account on https://test.pypi.org

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ maven-protocol
```

### 3. Publish to PyPI

```bash
# Create account on https://pypi.org

# Create API token at https://pypi.org/manage/account/token/

# Upload to PyPI
twine upload dist/*

# Or configure in ~/.pypirc:
```

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZw...
```

### 4. Automate with GitHub Actions

The release workflow (`.github/workflows/release.yml`) will auto-publish when you create a GitHub release:

```bash
# Tag version
git tag v0.1.0
git push origin v0.1.0

# Or create release via GitHub web interface
gh release create v0.1.0 --title "v0.1.0 - Initial Release" --notes "Initial beta release of MAVEN"
```

---

## Development Workflow

### Daily Development

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes and test
# ... edit code ...
pytest tests/ -v

# 4. Format and lint
black src/ tests/
ruff check --fix src/ tests/
mypy src/

# 5. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: add my feature"

# 6. Push and create PR
git push origin feature/my-feature
gh pr create --title "Add my feature" --body "Description of changes"
```

### Version Bumping

```bash
# Update version in src/maven/__init__.py
# Update version in pyproject.toml
# Update CHANGELOG.md

git add .
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push origin main --tags
```

---

## Troubleshooting

### Tests Failing

```bash
# Clear pytest cache
pytest --cache-clear

# Reinstall in editable mode
pip install -e ".[dev]" --force-reinstall

# Check for import issues
python -c "import maven; print(maven.__file__)"
```

### GitHub Actions Failing

- Check the Actions tab for error logs
- Ensure all secrets are set correctly
- Test locally: `act` (GitHub Actions local runner)

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to .venv

# Reinstall package
pip install -e .
```

---

## Best Practices Checklist

- [ ] All tests passing locally
- [ ] Code formatted with Black
- [ ] No linting errors from Ruff
- [ ] Type checking passes with mypy
- [ ] Coverage > 80%
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow conventional commits
- [ ] Branch protection enabled on `main`
- [ ] CI passing on GitHub
- [ ] Pre-commit hooks installed

---

## Quick Reference Commands

```bash
# Development
pip install -e ".[dev]"          # Install for development
pytest tests/ -v --cov=maven     # Run tests with coverage
black src/ tests/ examples/      # Format code
ruff check --fix src/            # Lint and fix
mypy src/                        # Type check

# Git
git checkout -b feature/name     # Create feature branch
git add .                        # Stage changes
git commit -m "type: message"    # Commit with conventional message
git push origin feature/name     # Push to GitHub
gh pr create                     # Create pull request

# GitHub
gh repo view --web               # Open repo in browser
gh pr status                     # Check PR status
gh workflow view                 # View workflows

# Publishing
python -m build                  # Build package
twine check dist/*               # Validate package
twine upload dist/*              # Upload to PyPI
```

---

## Next Steps

1. ✅ Initialize Git and push to GitHub
2. ✅ Set up virtual environment and install dependencies
3. ✅ Configure API keys
4. ✅ Run all tests locally
5. ✅ Set up pre-commit hooks
6. ✅ Configure GitHub repository settings
7. ✅ Test CI/CD pipeline
8. 📝 Write additional tests
9. 📝 Add more examples
10. 📝 Create GitHub release when ready

---

**Support:** Open an issue on GitHub or start a discussion for help!
