---
name: 20260903-203000-am-fullday-run-separated
description: Fixed the intraday-pipeline workflow bug where am and full_day predictions ran in the same job step at the same trigger, producing identical files.
type: feedback
---

**Bug:** `.github/workflows/intraday-pipeline.yml`'s single `prediction-am` step-decider branch (`H_ICT >= 8`) gated one job step, "Run Prediction Capture (AM & Full Day)", that called `predictions_loader.py --session am` and `--session full_day` back-to-back. Both hit the same PSI Engine response in the same run, so `predictions/{date}-{time}-am.json` and `-full_day.json` came out byte-identical (same `observationDate`, `psiScore`, `predictedRegime`) — confirmed on 2026-09-03. This directly fed the RFC 017 finding that `full_day` currently carries no information beyond `am`.

**Fix:** Split the step-decider into two separate time windows — `H_ICT >= 8` → `prediction-am`, `H_ICT >= 9` → `prediction-full-day` (both still before the 10:00 ATO/lookahead cutoff) — and split the single workflow step into two independently-gated steps, each calling only its own session. Added `prediction-full-day` to the `workflow_dispatch` choice list. The `all` dispatch option still runs both, as intended for manual full-cycle testing.

**Why this matters for future sessions:** If `am`/`full_day` (or any other pair of session captures) are still producing identical output after this fix, check whether they're both gated by the same step-decider branch or whether the workflow_dispatch `all` path is being used in production instead of the scheduled range logic (the `schedule:` cron trigger is currently commented out in this workflow — only `push` and `workflow_dispatch` fire it).
