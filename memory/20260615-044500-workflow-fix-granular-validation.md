# Workflow Trigger Fix & Granular Validation Support

**Date:** 2026-06-15 04:45:00 ICT
**Status:** Complete

## Context

The user reported that the `intraday-pipeline.yml` workflow did not run for a specific prediction file on 2026-06-14. Investigation revealed that the workflow _did_ run (triggered by a push), but the validation engine was overwriting the results because it used a single file per date. Additionally, the scheduled runs did not occur because it was a Sunday (market closed).

## Changes

### 1. Workflow Configuration (`.github/workflows/intraday-pipeline.yml`)

- Added `.github/workflows/**` and `predictions/**` to the `push` paths.
- This ensures that updates to the workflow logic or manual prediction uploads trigger the full cycle.

### 2. Validation Engine (`scripts/python/validation_engine.py`)

- **Granular Output**: Changed the output filename from `YYYY-MM-DD.json` to include the specific prediction timestamp (e.g., `2026-06-14-115424.json`).
- **Multiple Snapshots**: The engine now supports multiple validation records per day without overwriting.
- **Improved Metadata**: Corrected `@id` references in the JSON-LD output to point to the actual filenames.

### 3. Dashboard (`dashboards/app.js`)

- Updated the history table to display the `file_id` (timestamped) instead of just the date, providing better resolution for intraday analysis.

## Verification

- Ran `uv run pytest tests/python` - **78 PASSED**.
- Ran `uv run scripts/python/validation_engine.py` - Metrics successfully aggregated with new format.
- Checked `reports/metrics.json` - History now includes `file_id`.

## Future Considerations

- Market day logic: The scheduler is set to `1-5` (Mon-Fri). If weekend testing is required, the cron schedule needs temporary modification.
