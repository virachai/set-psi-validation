# PSI Dashboard Visualization Requirements (v01)

## 🎯 Objective
Define the operational requirements for the PSI Validation Dashboard to provide clear, actionable insights into model performance.

## 📊 Core Metrics
1. **Accuracy (Overall)**: Percentage of correct regime predictions.
2. **Hit Rate (Per Regime)**: Accuracy metrics for each specific regime (Bullish, Bearish, etc.).
3. **Confusion Matrix**: Heatmap showing predicted vs. actual regime distributions to identify systematic bias.
4. **Error Trend**: Visualization of `deviationScore` over time.

## 🖥️ Visualization Components
- **Summary Cards**: High-level KPI metrics (Accuracy, F1-Score).
- **Regime Matrix**: Interactive confusion matrix to highlight where the model struggles.
- **Timeline View**: Chronological chart displaying predicted vs. actual regime alignment.

## ⚙️ Technical Requirements
- **Data Source**: Consumes processed validation files from `data/processed/`.
- **Format**: Static site export (GitHub Pages compatible).
- **Design Principle**: Lean, high-contrast, data-dense.

---
**Status**: Draft for Review
**Governance**: Compliant with "Lean PSI Validator" principles.
