# MAVEN Protocol Specification

**Version:** 1.0.0-beta
**Status:** Draft

## 1. Overview

MAVEN is a protocol for multi-model verification through structured dialogue and consensus-building.

## 2. Core Principles

1. **Non-hierarchical**: No model has inherent authority over others
2. **Role-based**: Models operate within assigned behavioral constraints
3. **Iterative**: Verification proceeds through multiple rounds until consensus
4. **Transparent**: All reasoning is captured in an audit trail

## 3. Roles

### 3.1 Architect
- Proposes initial response with detailed reasoning
- Must provide evidence or logical justification
- Responds to challenges with clarification or revision

### 3.2 Skeptic
- Identifies potential errors, gaps, or unsupported claims
- Asks probing questions
- Does not propose alternatives (only challenges)

### 3.3 Mediator
- Synthesizes discussion into potential consensus
- Identifies points of agreement and disagreement
- Proposes resolution paths

## 4. Protocol Flow

```
1. INITIALIZE
   - Assign roles randomly to models
   - Prepare query context

2. PROPOSE (Architect)
   - Generate initial response
   - Include reasoning chain

3. CHALLENGE (Skeptic)
   - Review proposal
   - Identify weaknesses
   - Pose questions

4. RESPOND (Architect)
   - Address challenges
   - Revise if needed

5. SYNTHESIZE (Mediator)
   - Evaluate exchange
   - Propose consensus position

6. CHECK CONSENSUS
   - If 3/3 agree: EXIT with consensus
   - If 2/3 agree: EXIT with documented dissent
   - If no consensus: ROTATE roles, GOTO step 2
   - If max iterations: EXIT with best answer

7. OUTPUT
   - Final answer
   - Confidence score
   - Complete trace
```

## 5. Message Format

Messages use JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "method": "verify",
  "params": {
    "query": "string",
    "iteration": 1,
    "role": "architect|skeptic|mediator",
    "context": {}
  },
  "id": "uuid"
}
```

## 6. Consensus Detection

Consensus is determined by semantic similarity analysis:

1. Extract key claims from each response
2. Compare claims across models
3. Calculate agreement score
4. Threshold: 0.8 for full consensus

## 7. Exit Criteria

| Condition | Action |
|-----------|--------|
| 3/3 models agree | Return consensus |
| 2/3 models agree | Return consensus with dissent noted |
| Max iterations reached | Return best answer with low confidence |
| Critical error | Return error with partial trace |

## 8. Trace Format

```json
{
  "trace_id": "uuid",
  "query": "original query",
  "started_at": "ISO timestamp",
  "completed_at": "ISO timestamp",
  "iterations": [
    {
      "number": 1,
      "steps": [
        {
          "role": "architect",
          "model": "model-id",
          "content": "response text",
          "timestamp": "ISO timestamp"
        }
      ]
    }
  ],
  "result": {
    "consensus": "final answer",
    "confidence": 0.95,
    "dissent": null
  }
}
```
