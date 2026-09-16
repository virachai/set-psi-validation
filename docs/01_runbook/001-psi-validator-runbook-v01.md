# 001-psi-validator-runbook-v01.md

## Overview

This runbook covers daily operations for the PSI Validation pipeline.

## 1. Daily Intraday Workflow

The pipeline runs from one wide-window dispatcher (`intraday-pipeline.yml`). Its step-decider maps the current ICT time to a step; the canonical windows are below.

| Window (ICT) | Step                | Command                                                                                   |
| :----------- | :------------------ | :---------------------------------------------------------------------------------------- |
| 08:00–08:59  | AM Prediction       | `uv run scripts/python/predictions_loader.py --session am`                                |
| 09:00–09:59  | Full-Day Prediction | `uv run scripts/python/predictions_loader.py --session full_day`                          |
| 10:00–12:29  | ATO Capture         | `uv run scripts/python/capture_market.py --mode ato --symbol ^SET.BK --provider yahoo`    |
| 12:30–12:59  | Noon Capture        | `uv run scripts/python/capture_market.py --mode noon --symbol ^SET.BK --provider yahoo`   |
| 13:00–14:29  | PM Prediction       | `uv run scripts/python/predictions_loader.py --session pm`                                |
| 14:30–16:19  | PM Open Capture     | `uv run scripts/python/capture_market.py --mode pmopen --symbol ^SET.BK --provider yahoo` |
| 16:40–16:59  | ATC Capture         | `uv run scripts/python/capture_market.py --mode atc --symbol ^SET.BK --provider yahoo`    |
| 17:00–17:59  | Validation          | `uv run scripts/python/validation_engine.py`                                              |

Prediction windows are enforced by `MARKET_WINDOWS` in `predictions_loader.py` (a prediction outside its window is rejected); capture windows by `CAPTURE_WINDOWS` in `capture_market.py`.

## 2. Test & Verification

Use the unified test runner for all verification tasks:

- **Run all (Lint + Test + E2E):** `./scripts/sh/test.sh all`
- **Run only tests:** `./scripts/sh/test.sh test`
- **Run E2E smoke test:** `./scripts/sh/test.sh e2e`

## 3. Troubleshooting

- **Lookahead Bias:** If predictions are captured outside the window, check `predictions_loader.py` logs. Use `PSI_BYPASS_LOOKAHEAD=1` for manual testing.
- **Capture Window Guard:** `capture_market.py` refuses to run a mode outside its real ICT window (`CAPTURE_WINDOWS`: ato >=10:00, noon 12:30-14:00, pmopen 14:30-16:30, atc >=16:30), on the live *and* manual `--price` paths, so a mistimed run can never record one checkpoint's quote as another's. For a deliberate backfill use `PSI_BYPASS_WINDOW_GUARD=true`, which stamps `"windowGuardBypassed": true` on the record; to rebuild past dates from historical bars use `scripts/python/backfill_market_data.py`, which stamps `"backfilledFrom"`. CI fails if either bypass is enabled. See RFC 019.
- **Workflow Scheduling:** If GitHub Actions run out of sequence, verify the `step-decider` logic in `.github/workflows/intraday-pipeline.yml`.
- **Market Data Missing:** Check `logs/failures.jsonl` for API connection issues.
