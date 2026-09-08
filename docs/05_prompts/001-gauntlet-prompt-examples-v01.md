# 001-gauntlet-prompt-examples-v01.md

## Overview

This file contains categorized `gauntlet-loop` prompt examples tailored to the PSI Validation project, ensuring adherence to project mandates like lookahead bias prevention, PEP 723 standards, and type safety.

## Prompt 1: Hardening Pipeline Resilience

**Target:** Improving robustness against missing data in the validation pipeline.

> `/gauntlet-loop`
> **Goal:** Refactor `scripts/python/validation_engine.py` to handle asynchronous market data ingestion for the four-session cycle (Pre-ATO, ATO, Pre-ATC, ATC) without failing on missing files.
> **Quality Bar:**
>
> 1. Must handle missing JSON files in `market-data/` by logging a clear warning rather than crashing.
> 2. Maintain strict Python type hints.
> 3. Zero lookahead bias: Ensure no ATC data is accessed during PSI prediction derivation.
> 4. Must pass the E2E validation test defined in `docs/01_runbook/005-e2e-test-v01.md`.

## Prompt 2: Implementing New Regime Rules

**Target:** Expanding the research-to-code capability while ensuring data integrity.

> `/gauntlet-loop`
> **Goal:** Implement the 'volatility-spike' regime detection logic in `scripts/python/regime_rules.py`.
> **Quality Bar:**
>
> 1. Conform to the specifications in `docs/02_research_reports/010-market-regime-analysis-and-psi-thresholds-v01.md`.
> 2. Include comprehensive unit tests in `tests/python/test_regime_rules.py`.
> 3. Must not introduce lookahead bias: logic must rely strictly on available snapshot data.
> 4. Adhere to project type-hinting standards.

## Prompt 3: New Standalone Audit Script

**Target:** Creating portable, compliant utilities.

> `/gauntlet-loop`
> **Goal:** Create a standalone data audit script `scripts/python/audit_truth_layer.py` to verify consistency between `predictions/` and `market-data/`.
> **Quality Bar:**
>
> 1. Must include a PEP 723 metadata block (e.g., `# /// script ...`) for dependencies.
> 2. Must be fully type-hinted.
> 3. Must output results in a JSON format consistent with `reports/metrics.json`.
> 4. Must strictly adhere to the operational workflow defined in `docs/FLOW.md`.
