# Anomaly Log: High Pipeline Failure Rate (v01)

- **Date:** 2026-06-17
- **Anomaly:** 25% Job Failure Rate reported in GitHub Actions Metrics.
- **Context:** Pipeline runs successfully (Run time ~26s) but Dashboard classifies 25% of jobs as "Failed".

## 1. Observed Behavior

- **Job Status**: Workflow often shows "Red" (Failed) in Actions tab despite intended skips.
- **Run Time**: Extremely fast (Avg 16s), suggesting short-circuited execution.
- **Primary Hypothesis**: Intentional logic skips (e.g., Lookahead Bias protection or "step=none" condition) are being misclassified as CI job failures, or minor `exit 1` triggers during non-critical steps (like Git Commit) are skewing metrics.

## 2. Potential Culprits

- **`predictions_loader.py`**: Lookahead Bias check uses `return` (Exit 0) correctly for skips, but need to verify if `httpx` or `sys.exit(1)` triggers in edge cases are logging as full job failures.
- **`pytest`**: `Pre-commit Data Validation` step runs tests. Any test failure triggers `exit 1`, which is intended, but perhaps test environment issues cause intermittent failures.
- **`git commit` step**: The logic `git diff --staged --quiet || git commit ...` is designed to be idempotent, but if `git commit` fails for any reason (e.g., locked file, hook failure), it causes the job to crash.

## 3. Debugging Plan (Scheduled for 2026-06-17)

- [ ] Audit all scripts for `sys.exit(1)` triggers.
- [ ] Verify `git commit` behavior during CI runs.
- [ ] Investigate `pytest` logs for any silent errors/warnings treated as failures.
- [ ] Distinguish "Intentional Skips" from "True Failures" in future CI logs.

## 4. Current Status

- **DO NOT MODIFY CODE YET**.
- Pipeline logic remains functional and operational.
- Focus is on observation and metric validation.
