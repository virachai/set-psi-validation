# RFC 014: Lean Architecture & Data Truth Layer Enforcement (v01)

> **Document ID**: `014-rfc-lean-architecture-and-data-truth-layer-v01`  
> **Status**: Accepted / In Progress  
> **Author**: Principal System Architect & Lean Data Governance Specialist  
> **Reference**: [`docs/02_research_reports/009-lean-architecture-and-data-truth-gap-analysis-v01.md`](../02_research_reports/009-lean-architecture-and-data-truth-gap-analysis-v01.md)  
> **Effective Date**: 2026-09-02

---

## 🎯 Objective

This RFC outlines the concrete architectural simplifications and data integrity enforcements to transform the SET PSI Validation system into a **Lean, Verifiable, and Fail-Closed Truth Layer**.

---

## 1. Purge Synthetic Fallback Market Data ("Fail-Closed" Principle)

### Problem

`capture_market.py` previously contained fallback constants (`FALLBACK_ATO = 1500.0`, `FALLBACK_ATC = 1500.0`, `FALLBACK_VOLATILITY = 0.01`). When upstream market quote feeds failed or timed out, the system silently injected synthetic price data (yielding `0.0%` return), leading to false `Sideways` regime classifications.

### Specification

1. Completely remove all hardcoded fallback prices.
2. Implement **Fail-Closed** behavior: If an API provider fails to return valid quotes, log an explicit `ERROR` and abort capture.
3. No fake market data may enter the `market-data/` directory or participate in validation.

---

## 2. Unify Regime Derivation Engine (`scripts/python/regime_rules.py`)

### Problem

`capture_market.py` and `validation_engine.py` maintained identical copies of `derive_actual_regime()`. This violated the "Single Definition" principle and created divergence risk.

### Specification

1. Extract all market regime derivation thresholds and logic into a dedicated, importable module: `scripts/python/regime_rules.py`.
2. Standardize `VALID_REGIMES = ["Bullish", "Bearish", "Sideways", "Risk-Off", "Crisis", "Unclassified"]`.
3. Update `docs/010-regime-taxonomy-v01.json` to formally include the `Unclassified` term.

---

## 3. Stop Redundant Report Snapshots (Store Facts, Derive Metrics)

### Problem

Every execution of `validation_engine.py` wrote a new file to `reports/YYYY-MM-DD-HHMMSS-metrics.json` in addition to `reports/metrics.json`. These historical report snapshots duplicated rolling metrics already computable on-demand from `validation/*.json`.

### Specification

1. Remove creation of timestamped files in `reports/`.
2. Maintain exclusively `reports/metrics.json` as the deterministic build artifact consumed by the GitHub Pages dashboard.
3. The dashboard and metrics remain strictly downstream projections of the atomic validation facts.

---

## 4. Market Settlement Window Enforcement

### Problem

Running ATC market capture at exactly 16:30:00 ICT risks capturing pre-close intraday quotes before the SET closing auction settles (16:35–16:40 ICT).

### Specification

1. Set the minimum ATC capture time gate to **16:45:00 ICT**.
2. Workflows and scripts must enforce this time boundary to guarantee that only settled ATC prices are recorded.

---

## 5. Summary of Architecture Transitions

```text
BEFORE (Fragile & Fragmented):
  capture_market.py (with 1500.0 fallback + duplicate regime logic)
         │
  validation_engine.py (with duplicate regime logic + snapshot report bloat)
         ▼
  reports/YYYY-MM-DD-HHMMSS-metrics.json (redundant files)

AFTER (Lean & Verifiable):
  regime_rules.py (Single Canonical Logic)
         ▲                 ▲
         │                 │
  capture_market.py   validation_engine.py
   (Fail-Closed)       (Pure Reducer -> reports/metrics.json only)
```

---

## 6. Implementation Plan & Work Items

1. **[NEW] `scripts/python/regime_rules.py`**: Shared canonical regime classification engine.
2. **[MODIFY] `scripts/python/capture_market.py`**: Remove synthetic fallbacks, enforce fail-closed, import from `regime_rules.py`.
3. **[MODIFY] `scripts/python/validation_engine.py`**: Import from `regime_rules.py`, stop snapshot report emission.
4. **[MODIFY] `docs/010-regime-taxonomy-v01.json`**: Add `Unclassified` definition.
5. **[MODIFY] `tests/python/`**: Update test suite to verify fail-closed behavior, unified derivation, and clean report generation.
