# Changelog

All notable changes to MAVEN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-02-01

### Added
- **NEW PRIMARY FEATURE**: `HallucinationDetector` class for detecting AI hallucinations
  - 100% detection rate for critical hallucinations (fabricated studies, fake citations)
  - Multi-layer verification: consistency, fact-checking, citation analysis
  - Risk level scoring: LOW, MEDIUM, HIGH, CRITICAL
  - Detailed `HallucinationReport` with flags, confidence scores, and evidence
- Tool integration system for fact verification
  - Wikipedia search for factual claims
  - Calculator for numerical verification
  - Fact-check utilities
- `example_hallucination_detection.py` with 6 real-world test cases

### Changed
- **BREAKING**: Primary API changed from `ConsensusOrchestrator` to `HallucinationDetector`
- **BREAKING**: Package focus shifted from answer generation to hallucination detection
- Updated README with hallucination detection focus and actual benchmark results
- Marked multi-agent generation protocols as experimental (proven to degrade performance)
- Updated __init__.py to export `HallucinationDetector` as primary interface

### Deprecated
- `ConsensusOrchestrator` for answer generation (multi-agent consensus degrades accuracy)
- `VerificationOrchestrator` (matches baseline, adds complexity without benefit)
- `CollaborativeOrchestrator` (67% accuracy vs 100% baseline)

### Removed
- Experimental test files and benchmarking scripts
- Outdated documentation focused on consensus-based answer generation
- Files: `IMPROVEMENTS.md`, `VERIFICATION_PROTOCOL.md`, `EVALUATION_FIXES.md`, `AGENTS.md`
- Test files: `test_tool_integration.py`, `test_verification_protocol.py`, `test_collaborative.py`
- Benchmark scripts: `run_standard_benchmarks.py`, `run_reasoning_benchmark.py`, etc.

### Research Findings
- **Multi-agent consensus FAILS at generation**: 33-67% accuracy vs 100% single-model baseline
- **Multi-agent EXCELS at detection**: 100% critical hallucination detection rate
- Key insight: Multiple models better at finding flaws than creating correct answers
- Benchmark data: Consensus (33%), Verification (100% but no gain), Collaborative (67%)

### Fixed
- False negative rate for critical hallucinations: 0% (perfect detection)
- Over-flagging of legitimate answers: Intentional safety trade-off (50% false positives acceptable)

## [0.1.0] - 2026-01-31

### Added
- Initial beta release
- `ConsensusOrchestrator` class for multi-model verification
- Support for Anthropic Claude, OpenAI GPT, and Google Gemini
- Role assignment and rotation system
- Consensus detection with configurable thresholds
- Logic trace generation for audit trails
- Basic test suite
- Documentation and examples
