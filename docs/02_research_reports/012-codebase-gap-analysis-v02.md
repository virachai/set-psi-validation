# Codebase Gap Analysis v02 — Post-Remediation Commit

**Date:** 2026-09-16 21:28 ICT
**Scope:** Repository state after `95344b1` and its preceding remediation commits.

## Executive summary

The remediation round is materially in place and the automated Python test suite is green (`168 passed`). Static checks are also green except for one environment-specific Ruff `EXE002` caused by the mounted filesystem marking `predictions_loader.py` executable while Git records it as `100644`; this is not a committed executable-bit defect.

The second-pass audit found **no orphaned predictions and one historical missing prediction match**. More importantly, it exposed a remaining data-integrity issue in historical ATC artifacts: several `observationPeriod` end timestamps point to 2026-09-15 even though the files belong to earlier trading dates. This does not currently alter the regime values used by validation, but it makes the market-data truth layer internally inconsistent and can mislead downstream consumers.

## Verification performed

- `pytest`: **168 passed**
- `mypy scripts/python`: **no issues**
- `black --check scripts/python tests/python`: **clean**
- documentation naming validator: **success**
- out-of-window quarantine audit: **no current offenders**
- truth-layer audit: **0 orphans, 1 missing match**
- Git working tree: clean

## Findings

### G-01 — Historical ATC observation periods have incorrect end dates

**Severity:** High for data provenance; Medium for current scoring

Affected files include the ATC records for 2026-09-08 through 2026-09-14. Their `observationPeriod` ends at `2026-09-15T19:47:16/17+07:00` instead of the same trading date's ATC timestamp.

Example pattern:

```text
2026-09-09T10:00:00+07:00/2026-09-15T19:47:16+07:00
```

The flat `date`, ATO/ATC prices, and regime values are present, so current validation can still resolve truth. However, the schema.org temporal claim is false. Any downstream consumer that uses `observationPeriod` as the authoritative interval can associate a historical observation with the wrong day.

**Likely cause:** historical/backfill generation reused the current wall-clock time when constructing `period_end` rather than the capture's actual observation timestamp.

**Required fix:** rebuild affected historical ATC records with a deterministic period end derived from the ATC capture timestamp (or a documented fixed ATC observation time when only a historical price is available). Add a regression test that rejects an ATC record whose period crosses the `date` boundary.

### G-02 — Prediction and capture timing rules still have duplicated authorities

**Severity:** Medium

`predictions_loader.py` owns `MARKET_WINDOWS`, while `validation_engine.py` repeats the same three prediction windows as a separate literal table. `quarantine_out_of_window.py` imports `MARKET_WINDOWS`, so there are currently two authoritative representations rather than one.

This is a future drift risk: changing an environment default or session boundary in the loader can leave validation using a different boundary without a test necessarily detecting it.

**Required fix:** expose one shared window definition/module and import it from prediction capture, validation, and quarantine logic. If environment overrides are intentionally runtime-specific, provide a single resolver function rather than duplicating constants.

### G-03 — Workflow schedule is granular, but YAML execution is not parser-validated in the local toolchain

**Severity:** Low/Medium

The workflow now has nine cron entries and the step-decider aligns them with the intended ICT buckets. However, this environment did not have a YAML parser/actionlint available during verification, so the workflow was inspected textually rather than syntax-validated by a workflow-aware parser.

**Required fix:** add `actionlint` (or an equivalent workflow parser) to CI/pre-commit and validate `.github/workflows/*.yml` on every change.

### G-04 — Existing validation tests are still mostly unit-level, not end-to-end artifact-chain tests

**Severity:** Medium

The 168 tests prove individual guards and resolution functions, but the historical defect demonstrates that unit tests can pass while generated artifacts remain semantically wrong. There is no strong test that executes the chain:

`workflow/session decision → prediction artifact → market capture artifact → validation artifact → metrics`

with real timestamps and cross-file references.

**Required fix:** add fixture-driven end-to-end tests for each session, including valid boundaries, delayed execution, stale artifacts, missing market truth, and generated `observationPeriod` consistency.

### G-05 — Historical audit reports one unmatched market date

**Severity:** Low for runtime; Medium for archival cleanliness

`audit_truth_layer.py` reports one missing match: 2026-09-08 has market data but no retained prediction. This is consistent with the current prediction inventory: the prediction set begins on 2026-09-09 after the earlier AM artifacts were quarantined.

This should be explicitly classified as an intentional historical gap rather than silently treated as a healthy complete dataset.

**Required fix:** add an audit classification such as `expected_missing`, `unexpected_missing`, or a documented baseline date, so archival gaps are distinguishable from pipeline failures.

## Important non-findings

- Out-of-window AM predictions from 2026-09-09..16 are quarantined and no longer contribute to current metrics.
- Current retained predictions are full-day snapshots in the 09:00–10:00 ICT window.
- Full-day validation uses ATC/full-day truth rather than noon or PM-open truth.
- AM validation resolves from the dedicated noon observation; PM validation resolves from `afternoonRegime` in the ATC observation.
- The F1 zero-value regression is covered and the current metric output preserves valid zero values.
- The repository's Git index records Python scripts as non-executable except the intended quarantine script; the local `EXE002` is filesystem-mode noise, not a committed mode problem.

## Recommended next remediation order

1. **Fix G-01 first:** repair historical ATC `observationPeriod` values and add temporal-integrity tests.
2. **Remove duplicated window definitions (G-02).**
3. **Add workflow-aware linting (G-03).**
4. **Build an end-to-end artifact-chain test suite (G-04).**
5. **Classify the 2026-09-08 archival gap (G-05).**

## Acceptance criteria for the next round

A clean state should satisfy all of the following:

- every market-data observation period belongs to its declared trading date;
- every session window has one code-level source of truth;
- workflow YAML passes `actionlint`/equivalent validation;
- at least one end-to-end test exercises each AM/full-day/PM path;
- historical missing matches are explicitly classified; the 2026-09-08 ATC-only record is treated as `expected_missing` because it predates the earliest retained prediction (2026-09-09), while any market record on/after the retained prediction start is `unexpected_missing`;
- the full test + lint + type-check + docs + artifact audit pipeline remains green.
