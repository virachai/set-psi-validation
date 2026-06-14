# SET PSI Validation

PSI (Pressure-Signal Index) predicts **market regime**, not price.

This repository evaluates whether PSI-generated market regime forecasts correctly match the actual behavior of the Thai stock market (SET) within the same trading session.

---

## Core Idea

Most systems try to predict:

> "Will the market go up or down?"

PSI instead predicts:

> "What kind of market is this today?"

* Bullish
* Bearish
* Sideways
* Risk-Off
* Crisis

This repository validates whether that regime classification is correct in real market conditions.

---

## What is Being Validated?

We compare:

```text
PSI Predicted Regime (Pre-ATO)
            vs
Actual Market Regime (ATO → ATC)
```

---

## Intraday Workflow (SET Market)

```text
Pre-Market (Before ATO)
        ↓
Generate PSI Prediction
        ↓
Store Forecast Snapshot
        ↓
Market Open (ATO)
        ↓
Observe Intraday Behavior
        ↓
Market Close (ATC)
        ↓
Derive Actual Regime
        ↓
Validate Prediction
```

---

## PSI Prediction Example

```json
{
  "timestamp": "09:00:00",
  "date": "2026-06-14",
  "predicted_regime": "RISK_OFF",
  "psi_score": 0.41
}
```

---

## Market Outcome Example

```json
{
  "date": "2026-06-14",
  "ato": 1450.20,
  "atc": 1438.10,
  "return_pct": -0.83,
  "intraday_volatility": 1.95,
  "actual_regime": "RISK_OFF"
}
```

---

## How We Define Market Regimes

### Bullish

* Strong positive intraday return
* Broad-based market strength

### Bearish

* Consistent intraday decline
* Weak closing relative to ATO

### Sideways

* Low directional movement
* Range-bound trading

### Risk-Off

* Defensive behavior
* Increased volatility + downside bias

### Crisis

* Sharp downside move
* High volatility spike

---

## Validation Logic

We evaluate:

### 1. Regime Accuracy

```text
Predicted Regime == Actual Regime
```

### 2. Directional Consistency

* Bullish → Positive return
* Bearish → Negative return
* Risk-Off → Negative / defensive behavior

### 3. Confusion Matrix

Tracks misclassification between regimes.

---

## Key Metrics

### Classification Metrics

* Accuracy
* Precision
* Recall
* F1 Score

### Market Metrics

* ATO → ATC Return
* Intraday Volatility
* Directional Strength

### PSI Metrics

* PSI Score Distribution
* Regime Frequency
* Calibration Quality

---

## Repository Structure

```text
set-psi-validation/
├── predictions/     # PSI forecasts (pre-ATO snapshots)
├── market-data/     # SET ATO / ATC / intraday data
├── validation/      # evaluation logic
├── reports/        # performance analysis
└── dashboards/     # visualization outputs
```

---

## Use Cases

* Market Regime Validation
* Quant Research
* Signal Quality Assessment
* Risk Model Evaluation
* Intraday Market Behavior Study

---

## Important Note

PSI is not a trading signal.

It is a **market condition classifier**.

This repository exists to evaluate whether that classification is meaningful and statistically reliable.

---

## Disclaimer

This project is for research and educational purposes only.

It does not constitute financial advice or trading recommendations.

ถ้าคุณจะต่อยอด ecosystem นี้จริง ๆ โครงมันจะเริ่มเป็น 3-layer แล้ว:

```text
psi-engine        → generate regime
set-psi-validation → test correctness
psi-dashboard     → visualize performance
```

อันนี้คือ structure แบบ quant research pipeline ที่เริ่มดูเป็น “ระบบจริง” แล้วครับ
