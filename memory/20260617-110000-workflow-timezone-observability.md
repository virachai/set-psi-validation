# Memory: Workflow Timezone and Observability Improvements

**Date:** 2026-06-17
**Status:** Completed
**Component:** GitHub Actions Workflow, Operational Integrity

## Context

Previously, the intraday market cycle workflow suffered from counter-intuitive timezone mapping (UTC) and frequent "ghost run" failures. These failures occurred when the workflow was triggered out-of-schedule (e.g., manual push or GitHub cron delays) and attempted to commit changes when nothing was staged, leading to a "Failure" status in the CI pipeline.

## Improvements

### 1. Dual-Zone Step Detection

Refactored the `Determine Step` logic to check both **Asia/Bangkok (ICT)** and **UTC** hours simultaneously. This provides a redundant verification layer and makes the workflow logic directly align with the SET market schedule.

```bash
H_ICT=$(TZ='Asia/Bangkok' date +%H)
H_UTC=$(date -u +%H)
if [[ "$H_ICT" == "09" || "$H_UTC" == "02" ]]; then echo 'step=prediction-am' >> $GITHUB_OUTPUT; ...
```

### 2. Timezone Observability Logs

Added explicit logging to the CI console to print:

- **System Time (UTC)**
- **Market Time (ICT)**
- **Verification mapping** (ICT vs UTC hour comparison)

This allows for instant visual verification of whether the workflow is triggering at the intended time.

### 3. Execution Safety Guards

Implemented `if` conditions on all functional steps (Capture, Validation, Enrich, Commit) to skip execution if `step == 'none'`. This prevents the workflow from performing actions during invalid market hours.

### 4. Resilient Commit Logic

Updated the commit step to use `git diff --staged --quiet` to ensure a commit is only attempted if data artifacts were actually produced and staged. This eliminates the "nothing to commit" error that previously caused CI failures.

## Impact

- **Zero Ghost Failures**: Runs outside market hours now complete with a "Success" status by skipping irrelevant steps.
- **Improved Debugging**: Clear timezone logs in the CI console.
- **Operational Reliability**: Lookahead bias protection is now consistently applied based on verified ICT time windows.
- **Verified Success**: Run #107 (Push event) successfully demonstrated the lookahead bias gate skipping invalid windows while correctly capturing the PM session.
