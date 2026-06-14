# Decoupled Prediction Capture

## Metadata
- **Date:** 2026-06-14
- **Author:** Gemini CLI
- **Status:** COMPLETED

## Context
Decided to decouple PSI prediction capture from market data availability. Previously, the pipeline depended on both being present to proceed without errors. By separating these concerns, we ensure that PSI forecasts are captured independently of market data availability (e.g., weekends, holidays, or API outages).

## Changes Made
- Decoupled `predictions_loader.py` to always attempt to capture and store predictions, regardless of market data existence.
- Enhanced robustness in `predictions_loader.py` and `capture_market.py` for API authentication handling.

## Impact
- **Data Completeness:** The `predictions/` directory now acts as a reliable source of truth.
- **Backtesting Readiness:** Enables future backtesting even if historical market data is temporarily missing.
- **Improved Pipeline Stability:** Reduced CI pipeline failures.

## Next Steps
- Monitor the next scheduled run.

