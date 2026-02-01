# MAVEN Benchmark Results

## Executive Summary

Initial benchmark testing of MAVEN protocol against a single-model baseline using Together AI models.

**Test Date:** 2026-02-01
**Baseline Model:** Llama-3.1-8B
**MAVEN Models:** Llama-3.1-8B, Qwen-2.5-7B, Mixtral-8x7B
**Max Iterations:** 3
**Consensus Threshold:** 80%

## Quick Benchmark Results (5 Queries)

### Performance Metrics

| Metric | Baseline (Single Model) | MAVEN (Consensus) | Delta |
|--------|------------------------|-------------------|-------|
| **Accuracy** | 100% (5/5) | 60% (3/5) | -40% |
| **Avg Confidence** | N/A | 31.8% | - |
| **Avg Time** | ~1-2s per query | ~5-10s per query | 3-5x slower |

### Detailed Results

| # | Category | Question | Expected | Baseline | MAVEN | Confidence | Notes |
|---|----------|----------|----------|----------|-------|------------|-------|
| 1 | Geography | Capital of France? | Paris | ✓ | ✓ | 32.8% | Max iterations reached |
| 2 | Math | 15 + 27? | 42 | ✓ | ✓ | 33.8% | Dissent from Llama-3.1-8B |
| 3 | Science | Planets in solar system? | 8 | ✓ | ✗ | 49.3% | Over-qualified answer |
| 4 | Literature | Who wrote Romeo & Juliet? | William Shakespeare | ✓ | ✗ | 25.2% | Over-qualified answer |
| 5 | Science | Chemical symbol for gold? | Au | ✓ | ✓ | 18.0% | Max iterations reached |

### Key Findings

#### 1. Accuracy Issues

MAVEN performed **worse** than the single-model baseline:
- Baseline: 5/5 correct (100%)
- MAVEN: 3/5 correct (60%)
- **40% accuracy decrease**

**Failed Cases:**
- **Planets question**: MAVEN added unnecessary caveats about IAU definitions instead of simply answering "8"
- **Shakespeare question**: MAVEN qualified the answer with "overwhelming evidence supports" rather than directly stating "William Shakespeare"

#### 2. Low Confidence Scores

MAVEN's confidence scores were surprisingly low even for correct answers:
- Range: 18.0% - 49.3%
- Average: 31.8%
- Even simple factual questions like "capital of France" only achieved 32.8% confidence

This suggests the similarity calculation may be too conservative or the models are diverging on simple facts.

#### 3. Consensus Challenges

- **Max iterations reached:** 4 out of 5 queries (80%)
- **Dissent reported:** 2 out of 5 queries (40%)

The multi-agent debate frequently failed to reach consensus within 3 iterations, indicating:
- Models disagreeing on simple factual questions
- Potential over-analysis of straightforward queries
- Need for better consensus detection

#### 4. Performance Overhead

MAVEN is significantly slower than single-model inference:
- 3-5x time overhead
- Each query requires multiple iterations
- Each iteration calls 3 models (Architect, Skeptic, Mediator)

For simple factual queries, this overhead may not be justified.

## Analysis

### When MAVEN Struggles

Based on the benchmark results, MAVEN appears to struggle with:

1. **Simple factual questions** - Where a single model gives a direct, correct answer
2. **Over-qualification** - The debate process adds caveats and qualifications that hurt accuracy evaluation
3. **False dissent** - Models disagree on questions with clear, factual answers

### Potential Issues

1. **Prompt design** - Adversarial prompts may cause models to second-guess simple facts
2. **Similarity algorithm** - May not recognize paraphrased or qualified answers as equivalent
3. **Consensus threshold** - 80% may be too high for questions where models use different phrasing
4. **Role design** - Skeptic role may be too aggressive, creating unnecessary doubt

### When MAVEN Might Excel

The benchmark focused on simple factual queries. MAVEN may perform better on:
- **Complex reasoning** - Multi-step problems requiring analysis
- **Ambiguous questions** - Where multiple interpretations exist
- **Opinion-based queries** - Where diverse perspectives add value
- **Hallucination-prone tasks** - Where single models make up facts

## Recommendations

### 1. Adjust Consensus Parameters

```python
config = {
    'max_iterations': 5,  # Increased from 3
    'consensus_threshold': 0.7,  # Decreased from 0.8
}
```

### 2. Improve Answer Extraction

The evaluation showed MAVEN providing correct information but in verbose format. Need:
- Better structured answer extraction
- Recognition of qualified but correct answers
- More lenient similarity matching

### 3. Role Refinement

Consider:
- Less adversarial skeptic role for factual questions
- Task-specific role adjustments (factual vs reasoning)
- Confidence-based role behavior

### 4. Use Case Targeting

MAVEN should be positioned for:
- Complex, multi-step reasoning tasks
- High-stakes decisions requiring verification
- Ambiguous or nuanced questions

NOT for:
- Simple factual lookups
- Time-sensitive queries
- High-throughput applications

## Next Steps

1. **Run comprehensive benchmark** - Test on 100+ queries across difficulty levels
2. **Test on complex reasoning** - Try math proofs, logic puzzles, analysis tasks
3. **Benchmark against hallucination datasets** - TruthfulQA, HaluEval, etc.
4. **Tune consensus parameters** - Find optimal threshold and iteration count
5. **A/B test role prompts** - Compare adversarial vs collaborative approaches

## Full Benchmark Results (10 Queries)

### Performance Summary

| Metric | Baseline | MAVEN | Delta |
|--------|----------|-------|-------|
| **Accuracy** | 90.0% (9/10) | 70.0% (7/10) | **-20.0%** |
| **Avg Confidence** | N/A | 29.9% | - |
| **Avg Time per Query** | 1.09s | 27.47s | **25.3x slower** |
| **Avg Iterations** | 1 | 2.3 | - |
| **Max Iterations Hit** | 0% | 50% (5/10) | - |
| **Dissent Reported** | 0% | 100% (10/10) | - |

### Failed Cases Analysis

#### MAVEN Failures

1. **Capital of Australia** (Expected: Canberra)
   - Confidence: 17.8%
   - Status: Max iterations reached
   - **Issue**: Completely nonsensical answer about "Geographical Data Model" and "world geography databases"
   - **Root cause**: MAVEN produced meta-commentary about verification instead of answering the question

2. **Capital of Mongolia** (Expected: Ulaanbaatar)
   - Confidence: 11.9%
   - Status: Max iterations reached
   - **Issue**: Generic response about "alternative interpretations" and "review process"
   - **Root cause**: MAVEN went into meta-discussion mode instead of providing the factual answer

3. **Country with most time zones** (Expected: France)
   - Confidence: 25.2%
   - Status: Max iterations reached
   - **Issue**: Answered "Russia" (which is correct for mainland, but France has 12 total with overseas territories)
   - **Root cause**: Ambiguous question - both baseline and MAVEN got it "wrong" depending on interpretation

### Critical Findings

#### 1. Meta-Commentary Hallucinations

**Most Serious Issue:** MAVEN produced completely nonsensical "meta" responses for 2/10 queries:

```
Query: "What is the capital of Australia?"
Expected: "Canberra"
MAVEN: "The Geographical Data Model in the multi-model verification system is sourced
from multiple authoritative world geography databases, including the Australian Bureau
of Statistics, World Bank, and Unit[ed Nations]..."
```

Instead of answering, MAVEN started discussing verification methodologies. This is a critical failure mode.

#### 2. Performance Degradation

- **25.3x slower** than baseline
- Average 27.5 seconds per query
- Not viable for production use at this speed

#### 3. Low Confidence Despite High Consensus Similarity

Even correct answers had very low confidence:
- "Capital of France" (Paris): 36.9% confidence
- "Largest ocean" (Pacific): 17.4% confidence
- "Capital of Mongolia": 11.9% confidence (and wrong!)

#### 4. Consensus Failure Rate

- 50% of queries hit max iterations (5/10)
- 100% of queries reported dissent (10/10)
- Models frequently disagree on simple factual questions

### Detailed Results

Full results available in: `benchmarks/results/maven_benchmark_results.json`

## Root Cause Analysis

### Why MAVEN Underperformed

1. **Adversarial Prompting Issues**
   - Skeptic role too aggressive for factual questions
   - Causes models to second-guess simple facts
   - Leads to meta-discussions instead of direct answers

2. **Similarity Calculation Too Strict**
   - Different phrasings not recognized as equivalent
   - Low similarity → low confidence → poor consensus
   - Need better semantic matching

3. **Wrong Use Case**
   - MAVEN designed for complex reasoning and hallucination prevention
   - Simple factual lookups don't benefit from multi-agent debate
   - Actually performs worse due to over-complication

4. **Consensus Threshold Mismatch**
   - 80% threshold too high for diverse model responses
   - Even when all models agree on the fact, phrasing differs
   - Causes unnecessary iterations

## Conclusions

### Current State

MAVEN in its current form is **not suitable** for:
- ✗ Simple factual question answering
- ✗ High-throughput applications (25x slower)
- ✗ Time-sensitive queries
- ✗ Direct question-answer tasks

### Potential Fit

MAVEN **may be suitable** for (requires further testing):
- ? Complex multi-step reasoning
- ? Hallucination-prone creative tasks
- ? Ambiguous questions requiring nuanced analysis
- ? High-stakes decisions where verification overhead is acceptable

### Immediate Action Items

1. **Fix meta-commentary hallucinations** - CRITICAL
   - Adjust prompts to ensure direct answers
   - Add output validation to reject non-answers
   - Test with different role formulations

2. **Optimize performance**
   - Parallel model calls instead of sequential
   - Reduce iterations for simple queries
   - Add early stopping for high-confidence consensus

3. **Improve confidence calculation**
   - Better semantic similarity (embeddings?)
   - Handle paraphrasing and qualified answers
   - Calibrate to realistic confidence ranges

4. **Test on appropriate benchmarks**
   - TruthfulQA (hallucination detection)
   - Complex reasoning datasets (GSM8K, MATH)
   - Multi-step problems (HotpotQA)
   - Compare against single-model baselines

---

## Notes

This initial benchmark reveals important insights about MAVEN's current limitations on simple factual queries. However, these results should not be generalized to all use cases. MAVEN's true value proposition may lie in complex reasoning tasks where single models are more likely to hallucinate or provide incomplete answers.

Further testing on diverse query types and difficulties is needed to fully evaluate the protocol's effectiveness.
