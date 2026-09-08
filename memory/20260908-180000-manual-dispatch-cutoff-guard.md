---
name: manual-dispatch-cutoff-guard
description: Manual workflow_dispatch with an explicit single step (not 'auto'/'all') must tolerate capture_market.py lookahead-bias cutoff failures via continue-on-error, since the guard firing is expected behavior, not a bug.
metadata:
  pinned: false
---

`capture_market.py` enforces fail-closed lookahead-bias cutoffs (`_assert_before_cutoff`) for `noon`, `pmopen`, and `atc` captures: if the script is invoked after the mode's cutoff ICT time, it raises rather than writing a stale quote mislabeled as that checkpoint.

`.github/workflows/intraday-pipeline.yml` originally only set `continue-on-error: true` on the ATO/Noon/PM-Open/ATC capture steps when the step-decider resolved to `all`. A manual `workflow_dispatch` run with an explicit single step (e.g. `step=noon`) fired outside that mode's valid time window hits the same cutoff guard but was not covered by `continue-on-error`, so the whole job hard-failed even though the guard was working correctly — the "error" is the guardrail doing its job, not a defect in the capture logic.

Fix: extend `continue-on-error` on those four capture steps to also cover any `workflow_dispatch` trigger (`steps.step-decider.outputs.step == 'all' || github.event_name == 'workflow_dispatch'`), so an intentionally late/mistimed manual re-run fails soft (skips writing data) instead of reddening the whole pipeline run. Scheduled/push-triggered runs still fail hard if the cutoff guard fires unexpectedly, since that would indicate a real scheduling bug worth surfacing.
