---
name: Validation Engine Three-Window Analysis
description: Implementation of a validation engine supporting multiple intraday windows (AM, PM, Full Day) and aggregated rolling metrics.
type: project
---

The validation engine has been upgraded to support three-window (AM, PM, Full Day) regime analysis. This allows for granular performance tracking of PSI predictions against intraday market behavior.

**Why:** To move beyond daily binary accuracy and identify if PSI predictions have higher predictive power during specific intraday sessions (e.g., ATO vs. ATC).

**How to apply:** Use the new `--date` and `--recompute-all` flags in `scripts/python/validation_engine.py` to trigger the multi-window validation. Metrics are aggregated into `reports/metrics.json` including rolling 7D/30D accuracy per window.
