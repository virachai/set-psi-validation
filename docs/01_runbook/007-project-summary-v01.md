# Project Executive Summary: SET PSI Validation (v01)

## 🎯 Core Philosophy

The **SET PSI Validation** project serves as the "Truth Layer" for the PSI (Pressure-Signal Index) ecosystem. Its primary goal is to evaluate the accuracy of market regime predictions by comparing them against empirical market behavior.

- **Regime-Based Evaluation**: Focuses on market conditions (Bullish, Bearish, etc.) rather than simple price targets.
- **No Lookahead Bias**: Ensures strict temporal separation between prediction (Pre-ATO) and outcome (Post-ATC).

## 🕒 Intraday Execution Cycle (ICT Time)

1. **09:00 (Pre-ATO)**: Capture PSI Engine predictions.
2. **10:00 (Market Open)**: Capture ATO prices.
3. **16:30 (Market Close)**: Capture ATC prices and intraday metrics.
4. **17:00 (Validation)**: Derive actual regime and compute performance metrics.

## ⚖️ Actual Regime Derivation Logic

Market regimes are classified deterministically based on intraday returns and volatility:

- **Bullish**: Return > 0.5% & Low Volatility.
- **Bearish**: Return < -0.5% & Low Volatility.
- **Sideways**: Return within +/- 0.5%.
- **Risk-Off**: Return < -0.5% & High Volatility.
- **Crisis**: Return < -2.0% & Extreme Volatility.

## 📊 Data Architecture

The system uses a lean, file-based approach with standardized JSON schemas:

- **Prediction Snapshot**: Forecasted regime and PSI score.
- **Market Outcome**: Observed price action and volatility.
- **Validation Evaluation**: Comparison results (IsCorrect, DeviationScore).

## 🗺️ Roadmap & Visualization

- **Current Focus**: Core validation logic and schema standardization.
- **Next Steps**: Advanced metrics (F1-Score, Confusion Matrix) and rolling statistics.
- **Output**: A static, high-contrast dashboard hosted on GitHub Pages for transparency.

---

## 🌐 Schema.org Alignment

The PSI Validation data model has been formally mapped to [schema.org](https://schema.org) types for semantic interoperability:

| PSI Component             | Schema.org Type                  | Key Mapping                                              |
| :------------------------ | :------------------------------- | :------------------------------------------------------- |
| **Regime Taxonomy**       | `DefinedTermSet` + `DefinedTerm` | 5 market regimes as a controlled vocabulary              |
| **Prediction Snapshot**   | `Observation`                    | Pre-ATO forecast with `measurementMethod`                |
| **Market Outcome**        | `Observation`                    | ATO/ATC data via `variableMeasured`                      |
| **Validation Evaluation** | `Observation` + `marginOfError`  | `deviationScore` → `marginOfError` (direct 1:1)          |
| **Aggregated Metrics**    | `Dataset` + `AggregateRating`    | Accuracy as rating, F1/precision/recall as PropertyValue |
| **All Data**              | `DataCatalog`                    | Top-level container for all datasets                     |

Full mapping in [`docs/research_reports/008-schema-org-mapping-v01.md`](research_reports/008-schema-org-mapping-v01.md).

---

**Status**: Formalized Summary (Schema.org Mapping v01 Complete)
**Governance**: Compliant with `NNN-kebab-case-vNN.ext` naming convention.
