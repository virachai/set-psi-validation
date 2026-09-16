# Codebase Integrity Review v01

**Review date:** 2026-09-16
**Scope:** `set-psi-validation` (this repository). The first pass ran at `/workspace`, which is this same folder mounted into a Linux environment; every finding was then re-verified on the Windows checkout.
**Review type:** Static/code-path review, test/lint/type checks, CI/worktree/data-integrity inspection
**Status:** F-01 to F-04 resolved (commits below); F-05 deferred; F-06 withdrawn

## Executive summary

The repository shows no broad functional regression: the test suite passes (`168 passed` after remediation), and ruff, mypy and black are clean on the CI scope (`scripts/ tests/`).

Verification confirmed four real issues and withdrew one:

1. **Mixed line endings (F-01):** 118 working-tree files were CRLF while the index was LF, and 11 files had been committed to HEAD with CRLF. Windows git (`core.autocrlf=true`) hid this; the Linux mount did not.
2. **Out-of-window AM predictions scored as valid (F-03):** AM predictions captured at ~09:28 ICT on 2026-09-09 through 2026-09-16 fall outside the 08:00–08:59:59 AM window, yet five of them were still counted in aggregate metrics.
3. **F1 zero-value bug (F-04):** a defined precision/recall of `0.0` produced F1 `None`.
4. **AM schedule documentation drift (F-02):** runbooks still described AM prediction at 09:00 with a 10:00 cutoff.

The first pass also reported 23 ruff `EXE002` failures (F-06). They only appear on the Linux mount, where every file looks executable; CI checks out from git and passes.

## Environment notes

Two first-pass results came from running on a Windows folder mounted into Linux and must be read with that in mind:

| Observation on `/workspace`       | Cause                                                    | Real issue?            |
| --------------------------------- | -------------------------------------------------------- | ---------------------- |
| ~112 files changed in `git diff`  | Linux git has no `autocrlf`; working copies were CRLF    | Yes (F-01)             |
| 23 ruff `EXE002` violations       | The mount reports every file as executable               | No (F-06, withdrawn)   |

Use `git ls-files --eol` to check line endings and `git ls-files -s` to check executable bits; both reflect what CI sees.

## Evidence and checks

Results after remediation, on the Windows checkout:

| Check                                     | Result             | Interpretation                                                   |
| ----------------------------------------- | ------------------ | ---------------------------------------------------------------- |
| `uv run pytest -q`                        | **168 passed**     | Includes the new F1 zero-value test                              |
| `uv run mypy scripts/python tests/python` | **Pass**           | No type errors                                                   |
| `uv run black --check scripts/ tests/`    | **Pass**           | Formatting clean                                                 |
| `uv run ruff check scripts/ tests/`       | **Pass**           | Matches the CI and pre-commit scope                              |
| `uv run scripts/python/validate_docs.py`  | **Pass with skip** | Skips missing `docs/research_reports` (F-05)                     |
| `git ls-files --eol`                      | **209 i/lf**       | All tracked text files stored as LF, enforced by attributes      |

## Findings

### F-01 — Mixed CRLF/LF line endings

**Severity:** Medium (repository hygiene / merge risk)
**Status:** Resolved in `6d573a7`

Before the fix, `git ls-files --eol` reported 118 working-tree files as CRLF, 87 as LF and 3 as mixed, and 11 files stored in HEAD as CRLF (`FLOW.md`, `INDEX.md`, `docs/FLOW.md`, `scripts/python/audit_truth_layer.py` and others). Windows git's system-level `core.autocrlf=true` reduced the visible diff to 5 files, while git on the Linux mount showed ~112.

**Impact:** any tool or agent reading the folder without `autocrlf` sees thousands of phantom line changes, which hides real edits and inflates merge risk.

**Fix:** added `.gitattributes` with `* text=auto eol=lf`, converted working copies to LF and renormalized the 11 CRLF files in a standalone commit. `git show --ignore-cr-at-eol` confirms the commit changes line endings only.

### F-02 — AM prediction window inconsistent with runbooks

**Severity:** Medium (operational correctness)
**Status:** Resolved in `8f24ef2`

`scripts/python/predictions_loader.py` defines AM as `08:00:00`–`08:59:59` and full-day from `09:00:00`, and the workflow step-decider matches. Two runbooks disagreed:

- `docs/01_runbook/001-psi-validator-runbook-v01.md`: AM prediction at 09:00.
- `docs/01_runbook/006-workflow-timezone-debug-v01.md`: AM at 09:00 and `PSI_CUTOFF_AM` default `10:00:00`.

`docs/02_rfc/002-rfc-modular-intraday-pipeline-v01.md` already listed AM at 08:00 and needed no change.

**Fix:** both runbook schedule tables now list every step-decider window (AM, full-day, ATO, noon, PM, PM open, ATC, validation), and runbook 006 documents the `PSI_OPEN_*` / `PSI_CUTOFF_*` defaults.

### F-03 — Out-of-window AM predictions counted in metrics

**Severity:** High (data provenance / metric integrity)
**Status:** Resolved in `a1de9f3`

The first pass flagged only 2026-09-16. Verification found the same problem on every trading day from 2026-09-09 to 2026-09-16: each AM prediction was captured at 09:27:58–09:28:00 ICT, after the 08:59:59 AM cutoff, with the same timestamp as the full-day prediction. Five of the matching AM validation records (09-09 to 09-15) were still in `validation/` and counted in `reports/metrics.json`.

**Fix:** ran `scripts/python/quarantine_out_of_window.py --apply`, which moved 6 AM predictions and 5 AM validation records into the gitignored `quarantine/` directories (kept locally as an audit trail), then recomputed `reports/metrics.json`:

| Metric           | Before | After |
| ---------------- | -----: | ----: |
| Total records    |     11 |     6 |
| Overall accuracy |  54.5% |   50% |

Full-day predictions (09:00–10:00 window) were within their window and were not touched.

**Residual issues (not fixed):**

- `quarantine_out_of_window.py` selects validation records to move by session name only, not by date. It was correct here because every AM record was bad, but a future run could move valid records for other dates.
- With no AM records left, the AM session block in `metrics.json` reports accuracy `0.0` at `total_count` 0; `null` would state "no data" more accurately.

### F-04 — F1 metric zero-value bug

**Severity:** Medium (metric correctness)
**Status:** Resolved in `4124081`

`_compute_precision_and_f1()` in `scripts/python/validation_engine.py` used a truthiness check:

```python
if regime_precision and regime_recall:
    ...
else:
    f1[regime] = None
```

`0.0` is falsy, so a regime that was predicted and occurred but never matched reported F1 `None` instead of `0.0`.

**Fix:** `None` now means undefined (either input is `None`); a defined precision + recall of `0` yields `0.0`. Added `test_update_aggregate_metrics_f1_is_zero_not_none_when_all_wrong`, which failed before the fix and passes after.

### F-05 — Documentation validator treats a missing directory as success

**Severity:** Low
**Status:** Deferred (low impact)

`scripts/python/validate_docs.py` targets `docs/research_reports`, which does not exist (the real directory is `docs/02_research_reports`), and returns `True` when a target is missing.

**Recommendation:** point the target list at the real directory, or make a missing required directory fail.

### F-06 — Ruff `EXE002` on executable files without shebangs

**Status:** Withdrawn — only seen on the Linux mount

The 23 `EXE002` violations came from the mount reporting every file as executable. In git, only `scripts/python/quarantine_out_of_window.py` is marked `100755`, and it has a shebang. `ruff check scripts/ tests/`, as run by CI and the pre-commit hook, passes.

## Current architecture observations

The uncommitted working-tree changes to `validation_engine.py` and `predictions_loader.py` (present at review time, not part of the remediation commits) make validation fail closed:

- `find_latest_market_file()` requires an ATC file for full-day validation, with only the legacy `YYYY-MM-DD.json` fallback when it contains an actual regime.
- AM validation resolves from the dedicated noon capture rather than a full-day result.
- PM validation resolves from the ATC file's `afternoonRegime`.
- When the required market outcome is unavailable, `run_daily_validation()` skips writing a record instead of emitting a `pending` one.

These changes reduce the chance of scoring a prediction against the wrong market window.

## Remediation log

| Order | Finding | Commit    | Change                                                             |
| ----: | ------- | --------- | ------------------------------------------------------------------ |
|     1 | F-01    | `6d573a7` | `.gitattributes` (`eol=lf`) and renormalization of 11 CRLF files   |
|     2 | F-04    | `4124081` | F1 zero-value fix and regression test                              |
|     3 | F-03    | `a1de9f3` | Quarantine of AM artifacts 2026-09-09..16 and recomputed metrics   |
|     4 | F-02    | `8f24ef2` | Runbook 001 and 006 schedules synced with the step-decider         |

Frozen scope: F-01 to F-04 only. F-05 is deferred as low impact. F-06 is withdrawn. The two F-03 residual issues are recorded but not fixed.

## Conclusion

The codebase is not broadly broken, and the confirmed issues are fixed: line endings are normalized and enforced, out-of-window AM predictions no longer affect the metrics, F1 handles zero correctly, and the runbooks match the running schedule. Open items: F-05 and the two F-03 residual issues.
