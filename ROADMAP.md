# PSI Validation Ecosystem Roadmap (SET Market)

This roadmap defines a lightweight, focused system for evaluating and visualizing PSI (Pressure-Signal Index) performance in the Thai stock market (SET).

The ecosystem consists of only two active components:

* **SET PSI Validation** → correctness & evaluation layer
* **SET PSI Dashboard** → visualization layer

The PSI Engine is external (API) and not part of this repository scope.

---

## 1. System Architecture

```text id="arch1"
PSI Engine (External API)
        ↓
SET PSI Validation (Truth Layer)
        ↓
Evaluation Metrics + Aggregation
        ↓
SET PSI Dashboard (Visualization Layer)
```

---

## 2. SET PSI Validation

### Purpose

Validate whether PSI correctly predicts **market regime behavior** before market open (pre-ATO), and whether it aligns with actual market outcomes during the trading session.

---

### Core Concept

PSI does NOT predict price.

PSI predicts:

> Market Regime (Market Condition State)

* Bullish
* Bearish
* Sideways
* Risk-Off
* Crisis

---

### Workflow

```text id="flow1"
Pre-ATO
  ↓
Fetch PSI Prediction (External API)
  ↓
Store Prediction Snapshot
  ↓
ATO (Market Open)
  ↓
Capture Intraday Behavior
  ↓
ATC (Market Close)
  ↓
Compute Actual Regime
  ↓
Validate Prediction
```

---

### Validation Output Schema

```json id="schema1"
{
  "date": "2026-06-14",
  "predicted_regime": "RISK_OFF",
  "actual_regime": "RISK_OFF",
  "correct": true,
  "ato": 1450.20,
  "atc": 1438.10,
  "return_pct": -0.83
}
```

---

### Validation Logic

#### 1. Regime Accuracy

```text id="logic1"
Predicted Regime == Actual Regime
```

---

#### 2. Directional Consistency

* Bullish → ATC > ATO
* Bearish → ATC < ATO
* Risk-Off → negative / defensive behavior
* Sideways → low volatility / range-bound

---

#### 3. Confusion Matrix

Tracks misclassification patterns:

* Bullish → Bearish
* Risk-Off → Sideways
* Crisis → Bullish (critical failure case)

---

### Metrics

#### Classification Metrics

* Accuracy
* Precision
* Recall
* F1 Score

#### Market Alignment Metrics

* ATO → ATC return distribution
* Volatility alignment
* Regime stability

#### System Metrics

* Signal frequency per regime
* False signal rate
* Rolling accuracy (7D / 30D)

---

## 3. SET PSI Dashboard

### Purpose

Visualize PSI performance and validation results in a simple, static, GitHub Pages-based dashboard.

---

### Core Functions

* Display latest PSI prediction
* Show historical regime timeline
* Visualize accuracy metrics
* Display confusion matrix
* Track rolling performance

---

### Dashboard Sections

#### 1. Current Market State

* Latest PSI score
* Predicted regime
* Confidence indicator

---

#### 2. Performance Overview

* Overall accuracy
* Rolling 7D / 30D accuracy
* Regime-specific hit rates

---

#### 3. Time Series View

* PSI score over time
* Regime color overlay (Bull/Bear/Risk-Off/etc.)

---

#### 4. Confusion Matrix

* Visual representation of prediction errors

---

### Tech Stack

* GitHub Pages (static hosting)
* Vanilla JS or lightweight framework
* Chart.js / D3.js
* JSON-based data input

---

### Data Flow

```text id="flow2"
SET PSI Validation
        ↓
Export Aggregated JSON
        ↓
GitHub Pages Dashboard
        ↓
Visual Analytics
```

---

## 4. Milestones

### Phase 1 — Validation Core (Completed / In Progress)

* [ ] Standardize prediction schema
* [ ] Standardize market outcome schema
* [ ] Implement regime comparison logic
* [ ] Compute baseline accuracy

---

### Phase 2 — Evaluation Engine

* [ ] Confusion matrix implementation
* [ ] Rolling accuracy (7D / 30D)
* [ ] Regime-level performance breakdown
* [ ] Error classification analysis

---

### Phase 3 — Dashboard (GitHub Pages)

* [ ] Setup static site
* [ ] PSI time series visualization
* [ ] Performance summary UI
* [ ] Confusion matrix chart
* [ ] JSON pipeline integration

---

## 5. Final System View

```text id="final"
        PSI Engine (External API)
                   ↓
        SET PSI Validation Layer
                   ↓
        Aggregated Metrics / Truth Data
                   ↓
        SET PSI Dashboard (GitHub Pages)
```

---

## Guiding Principle

> PSI is not evaluated by prediction accuracy alone — but by whether it consistently describes real market behavior.

The validation layer is the “truth system” of PSI.

The dashboard is the “interpretation layer”.
