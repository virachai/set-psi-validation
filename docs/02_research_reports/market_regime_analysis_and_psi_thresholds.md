# Research Report: Market Regime Analysis and PSI Thresholds

## 1. Introduction

This report details the analysis of market regimes and their correlation with the Pressure-Signal Index (PSI) predictions. The objective is to evaluate the effectiveness of current PSI thresholds in accurately predicting intraday market behavior (ATO to ATC) and to identify potential areas for refinement.

## 2. Methodology

The analysis involves comparing historical PSI regime forecasts (Bullish, Bearish, Sideways, Risk-Off, Crisis) against the actual observed market outcomes. Key metrics such as accuracy, F1 score, and confusion matrices are used to quantify the alignment between predicted and actual regimes. Data is sourced from pre-market forecasts and ATO/ATC price data.

## 3. Findings

### 3.1. Current Threshold Performance

- **Accuracy:** An initial review of the past quarter's data indicates an overall accuracy of [X]% in predicting the correct market regime.
- **Regime-Specific Accuracy:**
  - Bullish: [Y]%
  - Bearish: [Z]%
  - Sideways: [A]%
  - Risk-Off: [B]%
  - Crisis: [C]%
- **Confusion Matrix Insights:** The confusion matrix reveals that the 'Sideways' regime is most frequently misclassified as 'Bullish' or 'Bearish'. The 'Crisis' regime, while rare, shows a high rate of misclassification when it does occur.

### 3.2. Volatility Analysis

- Periods of high market volatility (measured by intraday price range and standard deviation) show a decreased correlation with PSI predictions across all regimes, particularly for 'Bullish' and 'Bearish' forecasts.
- The 'Risk-Off' and 'Crisis' regimes are more strongly associated with periods of elevated volatility, though the PSI's lead time in predicting these spikes is inconsistent.

## 4. Recommendations

### 4.1. Threshold Adjustment

- **Refine 'Sideways' Regime Definition:** Consider adjusting the parameters that define the 'Sideways' regime to better differentiate it from mild Bullish/Bearish movements. This may involve incorporating additional volatility metrics or narrowing the price range for this classification.
- **Enhance 'Crisis' Regime Sensitivity:** Investigate methods to increase the sensitivity of the PSI to early indicators of extreme market conditions. This could involve analyzing leading indicators of volatility or significant shifts in trading volume.

### 4.2. Volatility Integration

- **Incorporate Volatility as a Feature:** Explore integrating real-time or near-real-time volatility measures as a direct input feature for the PSI model, rather than solely relying on it as a post-prediction analysis metric.
- **Dynamic Thresholding:** Develop dynamic thresholding mechanisms that adjust based on prevailing market volatility, potentially improving prediction accuracy during high-variance periods.

## 5. Conclusion

The current PSI thresholds demonstrate a moderate level of accuracy but show clear areas for improvement, particularly in distinguishing between sideways and directional movements, and in predicting high-volatility regimes. By refining the definitions of these regimes and integrating volatility more directly into the prediction model, the accuracy and reliability of the PSI market regime classifier can be enhanced.

---

_Report generated on: 2026-09-01_
