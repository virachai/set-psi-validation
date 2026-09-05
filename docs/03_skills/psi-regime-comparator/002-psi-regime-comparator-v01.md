---
name: psi-regime-comparator
description: Compares PSI regime hypothesis against actual intraday market behavior.
---

# PSI Regime Comparator Skill

## When to Use

Use this skill when validating whether the predicted PSI regime (Bullish, Bearish, Sideways, Risk-Off, Crisis) matches the observed intraday market outcome.

## Core Concepts

- **Alignment Verification**: Maps predicted regime to actual regime based on ATO/ATC price action and volatility.
- **Session-Truth**: Uses the validated session-aware regime as the ground truth.

## Quick Start

```bash
uv run scripts/python/validate_docs.py
```
