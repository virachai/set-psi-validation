# RFC: PSI Validation Pipeline Hardening (v01)

> **Status**: Partially Implemented — scope frozen 2026-09-07 (see §6)

## 1. Executive Summary

This RFC proposes a set of hardening measures to eliminate lookahead bias risks, improve metric granularity, and implement proactive observability for the PSI Validation Pipeline.

## 2. Problem Statement

The current pipeline exhibits several structural risks:

- **Lookahead Bias**: The `PSI_BYPASS_LOOKAHEAD` flag provides a silent path to invalidate backtest integrity.
- **Metric Masking**: Aggregating AM/PM sessions into a single daily mean hides intraday performance variance.
- **Silent Failures**: The fallback mechanism (`am` -> `noon` -> `full_day`) lacks explicit alerts when session-specific data is missing.
- **Binary Scoring**: `deviationScore` is too coarse to distinguish between minor and critical regime misclassifications.

## 3. Proposed Changes

### 3.1. Security Hardening — ✅ Implemented

- **CI Gate**: `.github/workflows/python-quality.yml` fails the build if `PSI_BYPASS_LOOKAHEAD=true`.
- **Runtime Guard**: `predictions_loader.py::validate_timestamp` raises `RuntimeError` (was: log-and-continue) when the bypass flag is set, so a stray env var can no longer silently invalidate the lookahead check.

### 3.2. Metric Granularity — ❌ Rejected (scope freeze)

- Session-wise `metrics.json` breakdown and mapping-based distance scoring were proposed but rejected on trade-off review: both add schema/logic complexity to the aggregation layer without a measurable gain in "did the PSI hypothesis predict correctly," which is out of scope per `010-lean-psi-validator-governance.md`. Not implemented.

### 3.3. Observability & Fail-Safe — Partially implemented

- **Heartbeat Check**: ❌ Rejected — a threshold-based CRITICAL alert was judged to add maintenance overhead (false positives) disproportionate to the benefit; not implemented.
- **Explicit Fallback Logging**: ✅ Implemented, in a leaner form than originally proposed. Rather than a `fallback_count` on aggregate metrics, `_resolve_market_outcome` now returns a `fallback_used: bool`, threaded through `run_daily_validation` into each validation record's `fallbackUsed` field. This gives per-record audit visibility into `am`/`pm` sessions scored against the full-day window, without adding new aggregation logic or alerting infrastructure.

## 4. Implementation Plan (as executed)

- **Phase 1** (done): CI gate + runtime guard for lookahead bypass.
- **Phase 2** (rejected): Session-wise metrics + distance scoring — descoped, see §3.2.
- **Phase 3** (rejected): Heartbeat alerts — descoped, see §3.3. Fallback logging shipped as a minimal per-record flag instead of a counter/alert.

## 5. Verification

- `tests/python/test_validation_engine.py::TestResolveMarketOutcome` covers `fallback_used` for all three sessions (am/pm/full_day, both fallback and non-fallback paths).
- Full suite: `uv run pytest tests/python/ -q` → 151 passed.

## 6. Scope Freeze Decision

Agreed 2026-09-07: only data-integrity fixes (lookahead bypass closure, minimal fallback audit trail) ship under this RFC. Metric-granularity and alerting proposals (§3.2, heartbeat in §3.3) are documented here for reference but explicitly not pursued, to keep the validator lean per governance. Revisit only if a concrete, measured need emerges — not preemptively.
