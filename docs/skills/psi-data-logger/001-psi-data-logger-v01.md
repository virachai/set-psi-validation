---
name: psi-data-logger
description: Standardized JSONL data logging for PSI predictions and market observations.
---

# PSI Data Logger Skill

## When to Use
Use this skill when capturing pre-market PSI predictions (Pre-ATO) or intraday market outcomes (ATO, Noon, PM Open, ATC) to ensure strict adherence to the project's unified JSONL formatting and timestamp conventions.

## Core Concepts
- **Deterministic Formatting**: All files must follow the `{date}-{time}-{suffix}.json` naming convention using ICT timestamps.
- **Fail-Closed Capture**: If data capture fails, record a explicit failure or pending status to prevent lookahead bias or missing records.

## Quick Start
```bash
uv run scripts/python/capture_market.py --mode ato --symbol ^SET.BK --provider yahoo
```
