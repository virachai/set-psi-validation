# SET PSI Validation: Market Regime Truth Layer

PSI (Pressure-Signal Index) is a quantitative framework designed to classify market regimes, not predict price movements. This repository serves as the **"Truth Layer"** for the PSI ecosystem, systematically validating pre-market predictions against intraday reality.

---

## 🎯 Value Proposition

In a landscape crowded with speculative price-prediction tools, **SET PSI Validation** focuses on **structural reliability** and **data-driven decision support**:

- **Engineering-First Rigor:** Enforces strict intraday workflows to eliminate lookahead bias—the silent killer of quantitative models.
- **Actionable Intelligence:** Transforms raw market data into semantic, `schema.org`-compliant observation records for cross-system interoperability.
- **Performance Accountability:** Provides a transparent "Scorecard" through Confusion Matrices and Rolling Metrics to assess model calibration in real-market conditions.
- **Lean, High-Impact Architecture:** A modular pipeline designed for low maintenance but high visibility into market behavior, serving as a critical piece of any robust quantitative research workflow.

---

## 🏛️ System Architecture

Our pipeline decouples **Prediction**, **Truth**, **Evaluation**, and **Interpretation**:

```text
PSI Engine (Predictor)
        ↓
Pre-ATO Prediction (Capture)
        ↓
SET Market (ATO → ATC Reality Extraction)
        ↓
Validation Engine (Truth Layer)
        ↓
Aggregated Metrics & Confusion Matrix
        ↓
SET PSI Dashboard (Visualization)
```

---

## ⚙️ Engineering Principles

1. **Lookahead Bias Prevention:** Strict session-specific cutoffs ensure that no future data pollutes forecast validation.
2. **Semantic Data Standards:** All data artifacts (Predictions, Market Records, Evaluations) conform to `schema.org` types, ensuring interoperability.
3. **Governance-Based Validation:** Derived actual regimes are tested against standardized, versioned taxonomy definitions.
4. **Reproducible Pipelines:** Modular, automated data ingestion and evaluation powered by `uv` and standard Python tooling.

---

## 📊 Key Metrics

Beyond simple accuracy, we quantify the PSI Engine's performance through:

- **Classification Metrics:** Accuracy, Precision, Recall, and F1 Scores per regime.
- **Confusion Matrix Analysis:** Identifying systematic regime misclassifications.
- **Calibration Quality:** Evaluating the relationship between the PSI Score and realized volatility/direction.
- **Rolling Performance:** 7D and 30D accuracy trends to observe adaptability to changing market cycles.

---

## 🛠️ Repository Structure

```text
set-psi-validation/
├── predictions/     # PSI forecasts (pre-ATO snapshots)
├── market-data/     # SET ATO / ATC / intraday data
├── validation/      # Intraday evaluation engine
├── reports/         # Aggregated performance metrics
└── scripts/         # Automated orchestration tools
```

---

## ⚠️ Disclaimer

This project is for research and educational purposes, serving as a robust **Decision Support System**. It does not constitute financial advice or trading recommendations.

---

## Governance

This project adheres to the **"Lean PSI Validator"** principles: **Actionable, Measurable, and Standardized.**
