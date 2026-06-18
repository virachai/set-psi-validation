---
name: 20260618-151000-crisis-regime-logic-fix
description: Fixed boundary condition in Crisis regime derivation logic (changed > to >=).
type: feedback
---

**Rule:** Use inclusive comparison (>=) for volatility threshold in Crisis regime derivation.

**Why:** The previous logic used `>` which caused a "Crisis" scenario with volatility exactly equal to the threshold (2x mean) to be misclassified as "Risk-Off". Boundary conditions must be inclusive to capture the intended regime at the threshold limit.

**How to apply:** Ensure all threshold checks in `derive_actual_regime` (both in `capture_market.py` and `validation_engine.py`) use `>=` for upper-bound volatility checks to prevent logic leakage into lower-severity regimes. Validated via `stress_test_regime.py`.
