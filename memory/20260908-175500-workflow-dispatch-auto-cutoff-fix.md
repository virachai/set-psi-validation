---
name: 20260908-175500-workflow-dispatch-auto-cutoff-fix
description: Added 'auto' default to workflow_dispatch, guarded closing auction transition, and tolerated expired captures in 'all' mode.
type: feedback
---

**Symptom:**
Manual or sequential execution of `intraday-pipeline.yml` in the afternoon / evening failed with:
`[ERROR] capture_market: noon capture attempted at 16:58:04 ICT, at/after the 14:00:00 ICT cutoff — the live quote no longer reflects the noon snapshot.`

**Root causes identified:**
1. `workflow_dispatch` defaulted to `step: "all"`, which sequentially triggered all steps (`prediction-am` -> `ato` -> `noon` -> `pmopen` -> `atc` -> `validation`). Because `noon` requires `ICT < 14:00` and `atc` requires `ICT >= 16:30`, running `all` on live quotes at any time of day was mathematically guaranteed to fail closed.
2. In `step-decider`, during 16:30–16:44 ICT, the check `H_ICT >= 14` matched, triggering `pmopen` after the 16:30 cutoff instead of holding for ATC settlement.
3. Cron at `:03/:33` had no scheduled trigger between 16:40 and 17:00 ICT to capture ATC upon settlement.

**Fixes applied in `.github/workflows/intraday-pipeline.yml`:**
1. Added `auto` option to `workflow_dispatch` and made it the default. When triggered manually without input, `step-decider` uses the time-based window resolver to execute only the step relevant to the current ICT time.
2. Added `elif [[ "$H_ICT" -eq 16 && "$M_ICT" -ge 30 ]]; then echo 'step=none';` to guard the 16:30–16:39 closing auction window against firing `pmopen` past its 16:30 cutoff.
3. Added dedicated ATC cron trigger `- cron: "48 9 * * 1-5"` (16:48 ICT) to automatically capture post-close ATC settlement.
4. Added `continue-on-error: ${{ steps.step-decider.outputs.step == 'all' }}` to live market capture steps so that explicit manual `all` executions tolerate expired temporal checkpoints without failing downstream steps.
