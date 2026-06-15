# RFC 011: PSI Validation Pipeline Refinements (v01)

## 🎯 Objective

This RFC proposes system refinements to address architectural gaps in volatility estimation, lookahead bias detection, and pipeline error observability.

---

## 1. Dynamic Volatility Threshold

- **Status**: Proposed
- **Problem**: The current `threshold_mean` used in regime classification is hardcoded to `0.02` (2%). This does not adapt to changing market cycles.
- **Proposed Solution**:
  - Compute a 30-day rolling standard deviation of the SET Index daily closing prices to derive the dynamic daily threshold.
  - Modify `capture_market.py` and `validation_engine.py` to calculate this value dynamically when fetching EOD data.

---

## 2. Advanced Volatility Indicator

- **Status**: Proposed
- **Problem**: The current volatility proxy is calculated as `(High - Low) / Open`, capped at 5%. This is a crude measure that ignores intraday variance.
- **Proposed Solution**:
  - Implement a daily Parkinson Volatility or standard log-return volatility metric:
    $$\sigma_{Parkinson} = \sqrt{\frac{1}{4 \ln 2} \ln\left(\frac{High}{Low}\right)^2}$$
  - This provides a more robust estimate of extreme price movements within the day.

---

## 3. Lookahead Bias Gate

- **Status**: Proposed
- **Problem**: There is no programmatic check to guarantee predictions were captured _before_ the market open (10:00 ICT).
- **Proposed Solution**:
  - Add a validation rule in `validation_engine.py` that compares the prediction file's `observationDate` timestamp against the market open timestamp of the same day.
  - If a prediction's timestamp is $\ge$ 10:00 ICT, the validation record is flagged as `Invalid` or rejected due to potential lookahead bias.

---

## 4. Pipeline Observability & Webhook Notifications

- **Status**: Proposed
- **Problem**: Errors or skipped executions run silently on GitHub Actions, requiring manual log inspection.
- **Proposed Solution**:
  - Integrate an optional notification handler in the scripts.
  - Support configuring a Slack or Discord webhook (`ERROR_NOTIFICATION_WEBHOOK` secret).
  - Automatically send alert cards on pipeline failures or validation anomalies.

---

**Effective Date**: 2026-06-16  
**Governance**: Compliant with "Lean PSI Validator" principles (Actionable, Measurable, Standardized).
