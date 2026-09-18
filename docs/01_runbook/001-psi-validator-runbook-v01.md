# 001-psi-validator-runbook-v01.md

## Overview

This runbook covers daily operations for the PSI Validation pipeline.

## 1. Daily Intraday Workflow

The pipeline runs from one wide-window dispatcher (`intraday-pipeline.yml`) on a single daily cycle (RFC 020). Its step-decider maps the current ICT time to a step; each window is retried on a schedule, and the scripts are idempotent.

| Window (ICT) | Step                   | Command                                                                                |
| :----------- | :--------------------- | :------------------------------------------------------------------------------------- |
| 05:00–09:59  | Full-Day Prediction    | `uv run scripts/python/predictions_loader.py --session full_day`                       |
| 16:45–23:59  | ATC Capture            | `uv run scripts/python/capture_market.py --mode atc --symbol ^SET.BK --provider yahoo` |
|              | + Validation (same step) | `uv run scripts/python/validation_engine.py`                                         |

The ATC capture window is enforced by `CAPTURE_WINDOWS` in `capture_market.py` (atc >= 16:30 ICT).

## 2. Test & Verification

Use the unified test runner for all verification tasks:

- **Run all (Lint + Test + E2E):** `./scripts/sh/test.sh all`
- **Run only tests:** `./scripts/sh/test.sh test`
- **Run E2E smoke test:** `./scripts/sh/test.sh e2e`

## 3. Troubleshooting

- **Lookahead Bias:** If predictions are captured outside the window, check `predictions_loader.py` logs. Use `PSI_BYPASS_LOOKAHEAD=1` for manual testing.
- **Capture Window Guard:** `capture_market.py` refuses to capture before 16:30 ICT (`CAPTURE_WINDOWS`), on the live *and* manual price paths, so a pre-close quote is never recorded as the ATC. For a deliberate backfill use `PSI_BYPASS_WINDOW_GUARD=true`, which stamps `"windowGuardBypassed": true` on the record; to rebuild past dates from historical bars use `scripts/python/backfill_market_data.py`, which stamps `"backfilledFrom"`. CI fails if either bypass is enabled. See RFC 019.
- **Workflow Scheduling:** If GitHub Actions run out of sequence, verify the `step-decider` logic in `.github/workflows/intraday-pipeline.yml`.
- **Market Data Missing:** Check `logs/failures.jsonl` for API connection issues.
