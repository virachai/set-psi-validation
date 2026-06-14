# PSI Ground Truth Regime Derivation Logic (v01)

## 🎯 Objective

Define a deterministic, rule-based logic to classify the `actualRegime` for a given trading day based on market behavior from ATO (Open) to ATC (Close).

## 📊 Inputs

- `ATO_Price`: Opening price.
- `ATC_Price`: Closing price.
- `Return_Pct`: `(ATC_Price - ATO_Price) / ATO_Price`
- `Volatility_Index`: (Proxy for intraday range/variance).

## ⚖️ Regime Classification Rules

| Regime       | Condition Logic                                                    |
| :----------- | :----------------------------------------------------------------- |
| **Bullish**  | `Return_Pct > 0.5%` AND `Volatility_Index < Threshold_Mean`        |
| **Bearish**  | `Return_Pct < -0.5%` AND `Volatility_Index < Threshold_Mean`       |
| **Sideways** | `abs(Return_Pct) <= 0.5%` AND `Volatility_Index < Threshold_Mean`  |
| **Risk-Off** | `Return_Pct < -0.5%` AND `Volatility_Index > Threshold_Mean`       |
| **Crisis**   | `Return_Pct < -2.0%` AND `Volatility_Index > (Threshold_Mean * 2)` |

## ⚙️ Operational Guardrails

1. **Thresholds**: `Threshold_Mean` must be calculated daily based on a 30-day rolling window of historical volatility to remain adaptive.
2. **Ambiguity Handling**: If a day meets criteria for two regimes (e.g., high volatility but positive return), it is flagged as `Unclassified` for manual review.
3. **Deterministic**: No heuristic adjustments; classification must be reproducible from raw price data.

---

**Status**: Draft for Review
**Governance**: Compliant with "Lean PSI Validator" principles (Simple, Actionable, Deterministic).
