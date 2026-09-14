---
name: prediction-window-lower-bound-gate
description: Added a lower-bound (window-open) check to predictions_loader.py's lookahead gate, closing a gap where workflow_dispatch step=all could pass validation for all sessions at once
metadata:
  pinned: false
---

# Prediction Window Lower-Bound Gate

## Problem

`scripts/python/predictions_loader.py`'s `validate_timestamp` only rejected a capture *after* a session's cutoff (`time_str > cutoff`), guarding against lookahead bias from late captures. It had no lower bound, so a capture far *before* a session's intended window passed validation. Concretely: `.github/workflows/intraday-pipeline.yml` has a `workflow_dispatch` input `step: all` that bypasses the time-gated `step-decider` logic entirely. A run fired at 02:27 ICT (well before market hours) passed validation for `am`, `pm`, and `full_day` simultaneously, since 02:27 is before every cutoff (10:00, 14:30, 10:00). The three per-day prediction files committed in `d35756b` (2026-09-14) all carry the identical timestamp `022758`, confirming this happened in practice.

This is not literal data-leakage (the API isn't fed future market data), but it defeats the intent of am/pm/full_day being independent forecasts captured progressively closer to each window — a `step=all` run collapses them into one API call reused three times.

## Fix (2026-09-14)

Added an `open` time per session in `MARKET_WINDOWS`, matched to the step-decider's actual per-session firing hours in the workflow (am 08:00, full_day 09:00, pm 13:00 ICT), and a `time_str < open_time` rejection alongside the existing cutoff check. Env overrides: `PSI_OPEN_AM`, `PSI_OPEN_PM`, `PSI_OPEN_FULL_DAY`. Added 4 tests in `tests/python/test_predictions_loader.py` covering premature-capture rejection for all three sessions and window-open boundary acceptance.

Pre-existing prediction files from before the fix (2026-09-11, 2026-09-14) were not backfilled or purged — they remain non-compliant with the new gate but weren't in scope for this change.

## Lesson

When a workflow has both a time-gated "auto" path and a manual bypass path (`workflow_dispatch step=all`), any guardrail meant to enforce timing semantics must validate against the *full* intended window (both bounds), not just the one direction the auto path already prevents by construction — the bypass path can silently violate the other direction.
