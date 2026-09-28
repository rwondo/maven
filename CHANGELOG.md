# Changelog

All notable changes to MAVEN are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - Unreleased

A smaller package that only checks answers, with the claims in the documentation cut back to what the code does.

### Removed
- The multi-agent debate code: `ConsensusOrchestrator`, `AsyncConsensusOrchestrator`, `VerificationOrchestrator`, `CollaborativeOrchestrator`, the role prompts, the similarity-based consensus scoring, and the calculator, Wikipedia and fact-check tools it used. It remains in git history at tags `v0.2.0` and `v1.0.0`.
- The MCP client. It never sent the MCP `initialize` handshake, and its documented example server does not exist.
- The LangChain and LlamaIndex wrappers. The LangChain callback handler crashed with a real `langchain-core` install.
- `DOMAIN_PROMPTS` and the `domain` argument (the prompts never used them), the `config` and `mcp_servers` arguments, `logic_checks`, `consistency_score` and `get_trace()`.
- The `docs/` folder, now covered by the README.
- Support for Python 3.9.

### Changed
- `confidence_score` is renamed `reliable_share`, since it is the share of models that voted RELIABLE. Reports now include each model's verdict.
- The CLI only runs detection: `maven --answer "..." "question"`. HIGH or CRITICAL risk returns exit code 3; the default reviewers are Together AI models.
- Dependencies have version ranges, dev tools are pinned in `requirements-dev.lock`, and ruff replaces black.
- Development status is Alpha.

### Fixed
- A missing API key was retried for about 18 seconds and then reported as MEDIUM risk. It now raises `ModelConfigError` immediately.
- Failed model calls counted as QUESTIONABLE votes. They now add a flag, so the result is at least HIGH risk.
- `AsyncHallucinationDetector.detect_batch()` mixed trace steps between concurrent runs.
- Verdicts in markdown (`**VERDICT:**`) or lower case were read as QUESTIONABLE, and "None identified" or "N/A" counted as findings.
- `maven --version` printed 1.0.0 for version 1.0.1.

### Added
- `scripts/evaluate_truthfulqa.py`, a balanced evaluation with confidence intervals and a flag-everything baseline.

### Corrections
- The TruthfulQA results in earlier releases (85.3% detection rate, 82% accuracy, "4% false positives") are withdrawn. Answers were labelled by exact substring matching, which marked 95 of 100 answers as untruthful, and the threshold was tuned on the same data. See the README for details.
- Also withdrawn: the claim that multi-agent debate lowered accuracy to 33–67% (a handful of questions, not reproducible), "100% critical hallucination detection" (2 of 2 hand-written examples), "5x faster" batch processing (never measured) and the "production-ready" label.

## [1.0.1] - 2026-02-01

### Changed
- Package published to PyPI as `maven-ai`; README and acronym wording updated.

## [1.0.0] - 2026-02-01

### Added
- `AsyncHallucinationDetector` with `detect_batch()`, a concurrency limit and progress callbacks.
- LangChain and LlamaIndex wrappers (removed in 2.0.0).

## [0.3.0] - 2026-02-01

### Added
- `detect_batch()` and `is_hallucination()` on `HallucinationDetector`.
- Rate limiting between API calls.
- `--detect` mode in the CLI.
- Domain prompt definitions (never used by the detector; removed in 2.0.0).

### Changed
- MEDIUM risk added to the default flagging threshold, and the risk rules redesigned around flags.
- The calculator tool evaluates expressions through the AST instead of `eval()`.

### Fixed
- Version mismatch between `__init__.py` and `pyproject.toml`.

## [0.2.0] - 2026-02-01

### Added
- `HallucinationDetector`: reliability votes, a fact check and a citation check, turned into a LOW/MEDIUM/HIGH/CRITICAL risk level with a report.

### Changed
- The project's focus moved from generating answers with a multi-model debate to checking answers with several models.

### Deprecated
- `ConsensusOrchestrator`, `VerificationOrchestrator` and `CollaborativeOrchestrator`.

## [0.1.0] - 2026-01-31

### Added
- `ConsensusOrchestrator`: three models take the roles of architect, skeptic and mediator and debate an answer over several rounds, with role rotation and a consensus check.
- Adapters for Anthropic, OpenAI, Google and Together AI models.
- Traces of every model call.
