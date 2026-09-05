---
name: psi-truth-metric-calculator
description: Calculates performance metrics including Accuracy, F1, and Confusion Matrix.
---

# PSI Truth Metric Calculator Skill

## When to Use

Use this skill when processing validated comparison logs to generate performance indicators for the PSI market regime classifier.

## Core Concepts

- **Truth Metrics**: Aggregates performance metrics (Accuracy, F1, Confusion Matrix) from validated comparison records.
- **Fail-Closed Reporting**: If insufficient data is available, report a null or pending status rather than hallucinating metrics.

## Quick Start

```bash
uv run scripts/python/validation_engine.py --calculate-metrics
```
