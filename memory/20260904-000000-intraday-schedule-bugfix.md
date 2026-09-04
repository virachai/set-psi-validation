---
name: 20260904-000000-intraday-schedule-bugfix
description: Fixed disabled/wrong-timezone cron and a step-decider elif ordering bug that made intraday captures skew to morning-only.
type: feedback
---

**Symptom:** User reported generated market-data files were "very messy, only ever generated for the morning session."

**Root causes found in `.github/workflows/intraday-pipeline.yml`:**

1. The `schedule:` cron trigger was commented out entirely, so the workflow only ran on `push` (to main, excluding data-path changes) or manual `workflow_dispatch`. Since GitHub Actions cron/schedule always runs in UTC, the original commented cron `*/30 7-20 * * 1-5` — despite its "ICT" comment — actually meant UTC 07:00-20:00 = ICT 14:00-03:00(+1), missing the entire morning market session (08:00-14:00 ICT) it was supposed to cover. This is almost certainly why someone disabled it and fell back to manual dispatch, which people run during Thailand daytime — hence data always landing in the morning steps.
2. `step-decider`'s elif chain checked `H_ICT == 14 && M_ICT >= 30` for the `pmopen` step, so only a 29-minute window (14:30-14:59) ever resolved to `pmopen`; every other afternoon hour (15:00-16:44) fell through to the `H_ICT >= 13` branch and incorrectly re-triggered `prediction-pm` instead of waiting for `atc`. This made the RFC 016/017 afternoon window (`pmOpenPrice` → `afternoonRegime`) very fragile to any Actions queue delay.

**Fix applied:**
- Cron restored as `*/30 0-13 * * 1-5` (UTC 00:00-13:59 = ICT 07:00-20:59), matching the actual comment's intent.
- `pmopen` condition widened from `H_ICT == 14 && M_ICT >= 30` to `H_ICT >= 14`, so it now correctly covers 14:00 through the `atc` cutoff (16:45).

**Why this matters for future sessions:** When any of this repo's GitHub Actions cron schedules look wrong or get silently disabled, check UTC vs ICT conversion first — this codebase's comments assume ICT but GitHub Actions cron is always UTC, and prior authors have made this mistake at least once already. Also, the step-decider's elif chain in `intraday-pipeline.yml` is order-sensitive and narrow single-hour equality checks (`H_ICT == N`) are a red flag — prefer `>=` range checks bounded by the next handler's own condition, as the surrounding branches already do.
