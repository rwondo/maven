# Standard Benchmark Results Analysis

## Date: 2026-02-01

## Summary: MAVEN Underperforms Across All Benchmarks

MAVEN performs **worse** than the single-model baseline on all three standardized benchmarks, including tasks specifically designed to test areas where multi-agent consensus should excel.

## Results Overview

| Benchmark | Task Type | Baseline | MAVEN | Delta |
|-----------|-----------|----------|-------|-------|
| **TruthfulQA** | Hallucination Detection | 80.0% | 60.0% | **-20%** ❌ |
| **GSM8K** | Math Reasoning | 100.0% | 60.0% | **-40%** ❌ |
| **MMLU** | General Knowledge | 100.0% | 80.0% | **-20%** ❌ |
| **Average** | - | 93.3% | 66.7% | **-26.7%** ❌ |

## Critical Findings

### 1. No Area of Excellence

MAVEN does not outperform the baseline on **any** benchmark category:
- ❌ **TruthfulQA** (hallucination detection) - where consensus should help catch misconceptions
- ❌ **GSM8K** (math reasoning) - where multi-step verification should improve accuracy
- ❌ **MMLU** (domain knowledge) - where multiple perspectives should validate answers

### 2. Worst Performance on Complex Reasoning

**GSM8K (Math)**: 100% → 60% (-40%)

This is particularly concerning because:
- Math problems have objective, verifiable answers
- Multi-step reasoning should benefit from verification
- Instead, MAVEN performs 40% worse than a single model

**Hypothesis**: The adversarial debate is causing models to:
- Second-guess correct answers
- Add unnecessary qualifications that break the evaluation logic
- Introduce errors through over-complication

### 3. Moderate Failure on Hallucination Detection

**TruthfulQA**: 80% → 60% (-20%)

MAVEN was specifically designed to reduce hallucinations through multi-model verification. The fact that it performs worse suggests:
- Models are not effectively catching each other's errors
- The skeptic role may be introducing doubt on correct answers
- Consensus is not filtering out misconceptions

### 4. Better But Still Worse on General Knowledge

**MMLU**: 100% → 80% (-20%)

While this is MAVEN's "best" performance, it's still 20% worse than baseline. This suggests the multi-agent approach adds confusion rather than clarity on factual knowledge.

## Performance Comparison Across All Tests

| Test Type | Baseline Accuracy | MAVEN Accuracy | Delta |
|-----------|------------------|----------------|-------|
| Simple Geography (10Q) | 90% | 90% | 0% |
| TruthfulQA (5Q) | 80% | 60% | -20% |
| GSM8K Math (5Q) | 100% | 60% | -40% |
| MMLU Knowledge (5Q) | 100% | 80% | -20% |
| **Overall Average** | **92.5%** | **72.5%** | **-20%** |

## Root Cause Analysis

### Why MAVEN Fails on Complex Tasks

1. **Over-complication**
   - Multi-agent debate adds verbosity
   - Verbose answers fail simple string matching
   - Example: Answer "42" becomes "The calculation shows that 15+27 equals 42, based on..."
   - Evaluation looks for "42" but gets lost in explanation

2. **Adversarial Harm**
   - Skeptic role introduces unnecessary doubt
   - Models second-guess correct answers
   - Creates disagreement where none should exist

3. **Consensus Confusion**
   - Different phrasings of the same correct answer
   - Similarity calculation fails to recognize equivalence
   - Leads to iterations that muddy the original correct answer

4. **Evaluation Mismatch**
   - Simple substring matching can't handle verbose responses
   - MAVEN's detailed answers don't match evaluation criteria
   - Need smarter evaluation or more concise answers

## Comparison to Hypothesis

**Original Hypothesis**: MAVEN should excel at:
- ✗ Complex multi-step reasoning (GSM8K: -40%)
- ✗ Hallucination-prone tasks (TruthfulQA: -20%)
- ✗ Ambiguous questions (no improvement anywhere)

**Reality**: MAVEN performs worse on all these tasks.

## Possible Explanations

### 1. Evaluation Logic Too Simple

The benchmark uses basic string matching:
```python
def evaluate_gsm8k(response: str, answer: str) -> bool:
    return answer in response
```

MAVEN's verbose responses might contain the answer but with too much surrounding text.

**Counter-argument**: Baseline also generates verbose responses but still scores 100%. The issue is likely MAVEN-specific.

### 2. Answer Extraction Failure

MAVEN may be providing correct reasoning but failing to extract/present the final answer clearly.

**Check needed**: Read actual MAVEN responses to see if answers are present but obscured.

### 3. Fundamental Flaw in Multi-Agent Approach

The adversarial debate may be inherently problematic:
- Creates doubt where certainty exists
- Prioritizes consensus over correctness
- Adds complexity that obscures simple truths

## Recommendations

### Immediate Actions

1. **Inspect Actual Responses**
   - Read MAVEN's responses for failed cases
   - Determine if answers are present but obscured
   - Check if evaluation logic is the problem or MAVEN is genuinely wrong

2. **Test Without Adversarial Roles**
   - Try collaborative vs adversarial prompts
   - Remove skeptic role, keep just voting/agreement
   - See if removing adversarial element improves performance

3. **Simplify Output Format**
   - Force MAVEN to output just the answer first
   - Add structured format: `FINAL_ANSWER: <answer>`
   - Ensure evaluation can extract answer from verbose text

4. **Consider Pivoting Use Case**
   - MAVEN may not be suitable for factual Q&A at all
   - Consider tasks where debate adds value:
     - Creative writing critique
     - Code review
     - Argument analysis
     - Ethical reasoning

### Long-term Questions

1. **Is multi-agent consensus fundamentally flawed for factual tasks?**
   - Evidence suggests yes for simple/medium complexity
   - May only help on extremely complex reasoning

2. **Should MAVEN be repositioned?**
   - Away from: Accuracy improvement
   - Toward: Transparency, explainability, uncertainty quantification
   - Value proposition: Not "more accurate" but "shows reasoning process"

3. **Is the speed/cost overhead ever justified?**
   - 20x slower for worse accuracy = No
   - Need to find tasks where MAVEN actually improves results

## Conclusion

**MAVEN's multi-agent consensus approach is not working as intended.**

Across all benchmarks tested:
- Simple factual queries: Equal to baseline (90% both)
- Hallucination detection: 20% worse
- Math reasoning: 40% worse
- General knowledge: 20% worse
- **Overall: 20% worse than single-model baseline**

The hypothesis that multi-agent verification would improve accuracy on complex reasoning and hallucination-prone tasks has been **disproven** by these benchmarks.

**Next Steps:**
1. Investigate why MAVEN fails (verbose answers vs actual errors)
2. Test alternative approaches (collaborative vs adversarial)
3. Find use cases where MAVEN actually helps, or
4. Acknowledge the approach doesn't improve accuracy for factual tasks

---

**Status**: MAVEN needs significant rethinking or repositioning. Current evidence suggests the multi-agent approach adds cost and complexity without improving accuracy.
