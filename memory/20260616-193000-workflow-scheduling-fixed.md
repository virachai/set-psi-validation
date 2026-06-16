# 20260616-193000-workflow-scheduling-fixed.md

## Context

The intraday pipeline was failing with "Lookahead Bias" errors during PM prediction capture. Investigation revealed that the GitHub workflow had multiple incorrect cron schedules that treated UTC hours as ICT (e.g., `0 14 * *` was intended as 14:00 ICT but executed at 21:00 ICT). Additionally, `push` triggers defaulted to running `all` steps, regardless of the current time.

## Changes

### 1. GitHub Workflow (`.github/workflows/intraday-pipeline.yml`)

- Removed duplicate and incorrect cron entries.
- Refined `step-decider` logic:
  - Scheduled runs now strictly map UTC hours to specific pipeline steps (`02` -> AM, `03` -> ATO, `07/08` -> PM, `09` -> ATC, `10` -> Validation).
  - Unexpected schedules now default to `step=none` instead of `step=all`.
  - `push` triggers still run `all` steps for testing, but are now handled gracefully by the scripts.

### 2. Prediction Loader (`scripts/python/predictions_loader.py`)

- Improved `validate_timestamp` logic:
  - If the run is NOT a GitHub scheduled run (`GITHUB_EVENT_NAME != "schedule"`), lookahead bias skips are logged as `WARNING` instead of `ERROR` and do not trigger `log_failure` (preserving `failures.jsonl` for legitimate production issues).
  - Added `PSI_BYPASS_LOOKAHEAD` environment variable to allow manual overrides for testing.

### 3. Utils (`scripts/python/utils.py`)

- Added `log_warning` to support non-critical event recording without polluting the failure log.

## Verification

- Validated UTC/ICT mapping for all 6 cron steps.
- Ran `pytest` suite; all 89 tests passed.
- Manually verified that `validate_timestamp` correctly distinguishes between scheduled and non-scheduled runs via env var simulation.
