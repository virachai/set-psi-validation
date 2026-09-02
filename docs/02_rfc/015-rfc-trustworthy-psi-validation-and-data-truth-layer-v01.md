---
slug: 015-rfc-trustworthy-psi-validation-and-data-truth-layer-v01
title: "RFC 015: Trustworthy PSI Validation & Data Truth Layer"
status: "Proposed"
date: "2026-09-02"
author: "Engineering Architecture Board & AI Agents"
target_version: "v2.1.0"
---

# RFC 015: Trustworthy PSI Validation & Data Truth Layer

## 1. Overview & Objective

This Request for Comments (RFC) outlines the architectural blueprint and 14-phase execution plan to transition the `set-psi-validation` system from a prototype validation pipeline into a fully trustworthy, auditable, and production-grade market-prediction validation system.

The core objective is to ensure that the system reliably answers the fundamental question:

> _"Given a prediction made at time $T$, using only information available at $T$, what actually happened in the market, was the prediction correct, and can another person reproduce and audit that result?"_

---

## 2. Core Principles & Non-Negotiables

1. **Data Truth & Provenance:** Never manufacture semantic equivalence (e.g., silently mapping ordinary daily Open/Close to auction ATO/ATC prices). Explicitly store data source provenance and separate market event time from capture time.
2. **Strict Lookahead Prevention:** Predictions must only be validated against market events occurring strictly after the prediction cutoff. Production environments prohibit lookahead bypass flags.
3. **Immutable Validation Records:** Historical validation records must never be silently overwritten or deleted. Integrity anomalies (e.g., orphaned predictions or missing market truths) must be represented explicitly.
4. **Deterministic Regime Rules:** Regime classification rules must be versioned (e.g., `regimeRuleVersion: "1.0.0"`) and centrally maintained.
5. **Accurate Temporal Metrics:** Rolling metrics (e.g., 7D/30D) must be computed over true trading days, preventing intraday sessions (AM/PM) from distorting day-based counts.
6. **Real Calibration & Baselines:** Connect numerical PSI confidence scores to empirical correctness (reliability curves/brier scores) and compare performance against trivial baselines (majority-class and previous-regime).

---

## 3. Implementation Phasing Strategy (14 Phases)

| Phase  | Title                | Summary of Actions                                                                                                                                              |
| :----- | :------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0**  | Inspection           | Audit prediction loader, providers, ATO/ATC logic, timestamps, and tests. Establish the codebase as the sole source of truth.                                   |
| **1**  | Market Truth         | Distinguish true auction observations (ATO/ATC) from standard OHLC. Fail loudly if auction data is missing rather than renaming open/close.                     |
| **2**  | Observation Schema   | Standardize versioned JSON observation schema incorporating market event time, source timestamp, and provenance metadata.                                       |
| **3**  | Timezone & Lookahead | Enforce `Asia/Bangkok` timezone universally. Build deterministic lookahead validation guards with explicit audit fields in validation records.                  |
| **4**  | Immutable Records    | Implement atomic file writes, check for exact validation record idempotency, and flag integrity mismatches without silent overwrites.                           |
| **5**  | Regime Taxonomy      | Centralize versioned rule configurations (`regimeRuleVersion`) and ensure deterministic boundary classification.                                                |
| **6**  | Rolling Metrics      | Restructure rolling metrics to compute strictly over unique trading days, accounting for multiple intraday sessions (AM/PM) correctly.                          |
| **7**  | Calibration Analysis | Map numerical PSI confidence scores to empirical correctness buckets, calculating calibration error and reliability metrics.                                    |
| **8**  | Baseline Comparison  | Introduce majority-class and previous-regime baselines to evaluate whether PSI outperforms trivial predictors.                                                  |
| **9**  | Metrics Rigor        | Enforce accurate statistical metrics (accuracy, precision, recall, F1, confusion matrix) with explicit null handling for zero-support classes and sample sizes. |
| **10** | Integrity Checks     | Implement a rigorous integrity layer detecting duplicate predictions, missing truth, invalid timestamps, and unsupported taxonomy versions.                     |
| **11** | Dependencies         | Audit and lock Python dependencies (`httpx`, `yfinance`, `pandas`, `numpy`) ensuring clean-room reproducibility.                                                |
| **12** | Test Suite           | Author comprehensive unit, integration, and regression tests covering all lookahead, regime boundary, and calibration edge cases.                               |
| **13** | Dashboard Alignment  | Ensure the static GitHub Pages dashboard exclusively consumes certified reports without re-deriving business logic.                                             |
| **14** | Documentation        | Update `README.md` and runbooks to reflect actual implementation semantics (what ATO/ATC means, timezone rules, calibration interpretation).                    |

---

## 4. Acceptance Criteria & Auditability

The implementation will be deemed successful only when:

- **No Synthetic Semantics:** ATO/ATC representation is grounded in true auction data or explicitly flagged as unavailable OHLC.
- **Reproducibility:** $\text{Prediction} + \text{Market Truth} + \text{Rule Version} = \text{Deterministic Validation Result}$.
- **Zero Lookahead Leakage:** Validation gates strictly block any prediction evaluated prior to market event cutoff.
- **Full Test Coverage:** 100% of new correctness constraints and regression fixes are backed by automated pytest suites.

---

_Approved by Architecture Board for immediate incorporation into the execution backlog._
