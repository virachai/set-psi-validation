# RFC-001: PSI Validation Pipeline Data Integrity and Remediation Plan

---

**Status**: Proposed / Active Review  
**Author**: Engineering Team  
**Scope**: `scripts/python/capture_market.py`, `scripts/python/validation_engine.py`, `scripts/python/predictions_loader.py`, `scripts/python/regime_rules.py`  
**Enforced By**: Lean PSI Validator Governance & Outcome-First Rules

---

## 1. Executive Summary & Objective

Recent forensic audits (`ai-105.json`) of the SET PSI Validation Pipeline revealed critical data-integrity flaws, fallback anti-patterns, and boundary mismatches across market data capture, truth resolution, and aggregate rolling metric calculations.

This RFC establishes the definitive specification and remediation plan to enforce **fail-closed data capture**, strict session boundary validation, proper trading-date rolling windows, and precise regime classification semantics.

---

## 2. Identified Vulnerabilities & Technical Debt

| ID         | Title                                                            | Severity     | Component               | Summary                                                                                       |
| ---------- | ---------------------------------------------------------------- | ------------ | ----------------------- | --------------------------------------------------------------------------------------------- |
| **ISS-01** | Reject ATC captures before official market close                 | **Critical** | `capture_market.py`     | Accepts generic latest market prices as completed ATC without time/session verification.      |
| **ISS-02** | Do not fall back from missing AM/PM truth to full-day truth      | **High**     | `validation_engine.py`  | AM/PM predictions fall through to full-day outcomes when dedicated truth windows are missing. |
| **ISS-03** | Calculate rolling 7D and 30D metrics by trading date             | **High**     | `validation_engine.py`  | Uses row-count rolling windows instead of actual trading dates across multi-session records.  |
| **ISS-04** | Reject missing/malformed market prices instead of 0.0 defaults   | **High**     | `capture_market.py`     | Silently substitutes zero or fallback values for missing OHLC components.                     |
| **ISS-05** | Do not replace missing ATO with Noon price                       | **High**     | `capture_market.py`     | Forces zero-return observations when ATO data is missing instead of failing closed.           |
| **ISS-06** | Require timezone-aware timestamps & validate trading date        | **Medium**   | `predictions_loader.py` | Parses naive timestamps and fails to enforce ICT trading date consistency.                    |
| **ISS-07** | Align Crisis regime boundary with documented threshold rule      | **Medium**   | `regime_rules.py`       | Uses `>= 2x` volatility threshold where documentation specifies `> 2x`.                       |
| **ISS-08** | Implement or document Precision, F1, and Calibration metrics     | **Medium**   | `validation_engine.py`  | README promises metrics not computed by aggregate reporting.                                  |
| **ISS-09** | Add freshness validation for market-provider observations        | **Medium**   | `providers.py`          | Provider abstraction lacks provider observation timestamps for freshness checks.              |
| **ISS-10** | Verify provider daily bars represent official SET auction prices | **Medium**   | `providers.py`          | Relies on generic Yahoo daily bars for session-specific auction checkpoints.                  |
| **ISS-11** | Make market-data writes atomic                                   | **Low**      | `capture_market.py`     | Writes JSON output directly without temp-file replacement.                                    |

---

## 3. Detailed Remediation Plan & Architectural Changes

### Phase 1: Fail-Closed Market Data Capture (`capture_market.py`, `providers.py`)

1. **Strict Session Boundary Enforcements**:
   - Implement rigorous time checks for ATC (`_capture_atc`), Noon (`handle_noon`), and ATO captures against official SET trading hours in `Asia/Bangkok` timezone.
   - Reject any capture attempt executed prior to the official session close or checkpoint time.
2. **Elimination of Numeric Defaults & Fabricated Prices**:
   - Prohibit substituting `0.0` or Noon prices for missing ATO/OHLC fields.
   - Enforce strict OHLC validation invariants:
     $$\text{high} \geq \max(\text{open}, \text{close}), \quad \text{low} \leq \min(\text{open}, \text{close}), \quad \text{high} \geq \text{low}$$
   - Require positive finite prices; fail closed and mark observation status as `incomplete` or `unclassified` on anomaly.
3. **Atomic File Writes**:
   - Replace direct JSON writes with atomic `os.replace()` pattern via temporary files in the target directory.

### Phase 2: Elimination of Truth Fallbacks (`validation_engine.py`)

1. **Isolated Session Truth**:
   - Remove fallback logic in `_resolve_market_outcome` where AM/PM predictions fall back to full-day outcomes.
   - Missing session truth must result in a `pending` validation status, excluding incomplete records from standard performance metrics.

### Phase 3: Accurate Trading-Date Metrics (`validation_engine.py`)

1. **Trading-Date Rolling Windows**:
   - Refactor `update_aggregate_metrics` to group validation records by distinct trading dates prior to calculating rolling 7-day and 30-day windows.
   - Prevent multi-session intra-day records from artificially inflating observation counts within rolling windows.

### Phase 4: Boundary & Timestamp Correctness (`regime_rules.py`, `predictions_loader.py`)

1. **Crisis Threshold Strictness**:
   - Update `derive_actual_regime` Crisis condition to strictly enforce `volatility_index > threshold_mean * 2` (or explicitly validate documentation alignment).
2. **Timezone Enforcement**:
   - Reject naive timestamps in `validate_timestamp`. Require ISO-8601 with explicit offsets and validate ICT calendar date matching.

---

## 4. Acceptance Criteria & Verification

- **Unit Test Coverage**: Add comprehensive `pytest` cases in `tests/` verifying fail-closed behavior on missing/zero prices, session boundary rejections, and calendar-date rolling calculations.
- **Data Integrity**: Zero synthesized zero-returns or pre-session complete artifacts allowed in validation runs.
- **Governance Compliance**: Fully aligned with Lean PSI Governance and Outcome-First rules.
