# RFC 020: Lean Single-Cycle Rollback

**Status**: Implemented
**Date**: 2026-09-18
**Author**: Dev AI Lead

## 1. Executive Summary

This RFC proposes a radical simplification of the intraday execution cycle, rolling back the multi-session features introduced in RFC 016/017 to return to a pure, single daily cycle. The goal is to perfectly align with the **Lean PSI Validator Governance** rule, eradicate chronic GitHub Actions scheduling delays, and drastically reduce codebase complexity.

The system will move from a 4-capture/3-prediction cycle to a **1-prediction/1-capture/1-validation** daily cycle.

## 2. Motivation & Problem Statement

**The Problem**:
GitHub Actions scheduled workflows (cron) are notoriously unreliable, often delaying or skipping jobs during peak UTC hours. Today (2026-09-18), the scheduler skipped all jobs between 10:00 and 12:00 ICT. Consequently, the `noon` capture job (Run #398) failed with a `RuntimeError` because it explicitly expected an `*-ato.json` artifact to have been created earlier in the day.

**The Irony**:
The live data provider (Yahoo Finance / SETSMART) naturally returns the day's Open (ATO) and Close (ATC) simultaneously. Running granular scripts 4 times a day forces artificial dependencies and introduces points of failure for data we could fetch reliably in a single daily call.

**The Lean Mandate**:
As stated in `AGENTS.md` and rule `010-lean-psi-validator-governance.md`, the sole purpose of the PSI Validator is to *"Measure whether your market hypothesis accurately predicts market behavior."* If the user's core hypothesis relies only on the morning prediction, retaining complex `noon`, `pm`, and `pmopen` splits violates the Lean Governance rule.

## 3. Proposed Architecture (Single Cycle)

The new pipeline will execute identically every trading day:

1. **05:00 - 09:59 ICT (Prediction Capture Retry Window)**
   - Capture the `full_day` prediction from the upstream engine.
   - Schedule: Run repeatedly (e.g., every 20-30 minutes) from 05:00 ICT until market open.
   - Idempotency ensures only the first successful capture writes the file.
2. **16:45 - 23:59 ICT (Market Capture & Validation Retry Window)**
   - Schedule: Run repeatedly (e.g., every 20-30 minutes) after market close until midnight.
   - Fetch the day's OHLC data from the live provider (extracting ATO and ATC).
   - Validate the morning prediction against the ATC market outcome immediately in the same continuous action step.
   - If the data was already captured and validated by an earlier run in this window, the script's idempotency (`_already_captured`) will safely skip the redundant execution.

## 4. Required Teardowns (Code Deletions)

This proposal requires deleting code rather than writing it. The following changes must be implemented:

### A. Pipeline Config (`.github/workflows/intraday-pipeline.yml`)
- **Remove**: All daytime intraday cron schedules.
- **Add/Retain**: A robust evening retry schedule (e.g., `cron: "45,05,25 9-16 * * 1-5"`) covering 16:45 ICT to 23:59 ICT, and a morning retry schedule for 05:00 to 09:59 ICT.
- **Remove**: The complex `step-decider` shell logic. Replace it with a simple step router that triggers Prediction in the morning (`prediction-full-day`) and Market Capture + Validation sequentially in the evening (`atc-and-validate`).
- **Remove**: Action steps for `ato`, `noon`, `prediction-pm`, `pmopen`, and standalone `validation`. Combine ATC capture and validation into one sequential step.

### B. Market Capture (`scripts/python/capture_market.py`)
- **Remove**: Arguments `--mode noon`, `--mode pmopen`, `--mode ato`. (The script defaults to ATC behavior).
- **Remove**: `handle_noon()`, `handle_pmopen()`, and `_resolve_afternoon_window()`.
- **Modify**: `handle_atc()` to stop loading existing ATO files (`load_existing`) and instead accept `ato_price` directly from `_fetch_live_prices`.

### C. Validation & Loaders (`scripts/python/validation_engine.py`, `scripts/python/predictions_loader.py`)
- **Remove**: `--session` argument mapping (e.g., `am`, `pm`, `full_day`).
- **Remove**: Session looping in `validation_engine.py` (e.g., `for session in SESSIONS:`). Validate exactly one file.

## 5. Backward Compatibility

- Existing data in `market-data/` and `predictions/` labeled with `-am`, `-pm`, `-noon`, etc., will remain untouched for historical audit purposes.
- New data will simply follow the `-full_day` and `-atc` naming conventions, maintaining compatibility with the dashboard generator.

## 6. Risks and Mitigations

- **Risk**: Loss of intraday granularity (measuring morning vs afternoon accuracy).
  - **Mitigation**: Acknowledged as acceptable loss in exchange for architectural stability. Intraday granularity was over-engineered for the current predictive scope.
- **Risk**: The single ATC capture fails.
  - **Mitigation**: Manually re-triggering the workflow once at any point after 16:30 ICT will fetch all required data and run validation automatically.

## 7. Next Steps

1. Approval of this RFC.
2. Delegate an engineering subagent to physically implement the code deletions and refactors across `.github/workflows` and `scripts/python/`.
