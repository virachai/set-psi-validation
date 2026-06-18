---
name: 20260618-144500-volatility-calculation-improvement
description: Optimized volatility calculation in capture_market.py by switching from open-price based to mid-price based normalization.
type: feedback
---

**Rule:** Use normalized volatility (mid-price base) for regime derivation.

**Why:** The original `(high-low)/open` formula was susceptible to distortion on days with significant opening price gaps, leading to potential misclassification of market regimes.

**How to apply:** Always use `mid_price = (high + low) / 2` as the denominator for intraday volatility calculations in `capture_market.py` to ensure consistency and robustness against price gaps. Validated via recomputation of all historical validation records.
