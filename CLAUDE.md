# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository implements a validation pipeline for the PSI (Pressure-Signal Index) market regime classifier for the SET (Thai Stock Market). It evaluates whether pre-market regime predictions (Bullish, Bearish, Sideways, Risk-Off, Crisis) align with actual intraday market behavior (ATO to ATC).

## Core Architecture

The system follows a strict daily intraday workflow:

1. **Prediction:** Fetch PSI regime forecast (Pre-ATO).
2. **Observation:** Capture market outcome (ATO price, ATC price, volatility).
3. **Validation:** Compare `Predicted Regime` vs `Actual Regime`.
4. **Aggregation:** Update performance metrics (Accuracy, F1, Confusion Matrix).
5. **Visualization:** Export results for the static dashboard (GitHub Pages).

## Development & Commands

### Running Validation

The validation pipeline is driven by Python scripts in `scripts/python/`.

- **Extract Market Data:**
  ```bash
  python scripts/python/extract_pdf.py
  ```
- **Validate Predictions:**
  ```bash
  python scripts/python/validate_docs.py
  ```

### Deployment

- **Deploy System:**
  ```bash
  ./scripts/sh/deploy.sh
  ```

### Setup

- **DeepSeek/Gemini Integration:**
  Use the setup scripts in `scripts/` to configure external model connectivity:
  ```bash
  ./scripts/setup_deepseek.sh
  ./scripts/Xsetup_gemini.sh
  ```

## Key Documentation

Refer to these files for the system logic:

- `FLOW.md`: Detailed intraday execution cycle.
- `ROADMAP.md`: Project milestones and roadmap.
- `README.md`: High-level PSI concept and regime definitions.
