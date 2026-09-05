---
name: modular-intraday-pipeline-refactor
description: Decomposed monolithic GitHub Action into modular, time-triggered workflows.
metadata:
  pinned: true
---

# Modular Intraday Pipeline Refactor

The monolithic `intraday-pipeline.yml` was successfully refactored into 8 independent GitHub Actions workflows, each mapped to specific market events (Prediction AM, Full Day, ATO, Noon, Prediction PM, PM Open, ATC, Validation). This transition improves observability, resilience, and maintainability by decoupling intraday stages and allowing precise cron scheduling. All new workflows follow the project's `uv` and `Git` standards.
