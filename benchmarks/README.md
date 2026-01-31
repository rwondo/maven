# MAVEN Benchmarks

This directory contains benchmark datasets and results for evaluating MAVEN's verification accuracy.

## Overview

The benchmarks compare:
- **Single Model**: One model answering directly
- **MAVEN (3 Models)**: Three models in adversarial consensus

## Datasets

### factual_queries.json

100 factual questions across multiple domains:
- Geography (25 questions)
- Science (25 questions)
- History (25 questions)
- Current Events (25 questions)

Each entry includes:
- `query`: The question
- `ground_truth`: The correct answer
- `category`: Domain category
- `difficulty`: easy/medium/hard

## Running Benchmarks

```bash
# Run full benchmark suite
python -m benchmarks.run_benchmarks

# Run specific category
python -m benchmarks.run_benchmarks --category science

# Compare models
python -m benchmarks.compare_models
```

## Metrics

| Metric | Description |
|--------|-------------|
| Accuracy | % of correct answers |
| Hallucination Rate | % of confident but wrong answers |
| Confidence Calibration | Correlation between confidence and accuracy |
| Latency | Average response time |
| Cost | Estimated API cost per query |

## Results

See [results/baseline_comparison.md](results/baseline_comparison.md) for current benchmark results.

## Contributing

To add new benchmark queries:
1. Add entries to the appropriate JSON file
2. Ensure ground truth is verifiable
3. Include source/citation if possible
4. Run validation script: `python -m benchmarks.validate`
