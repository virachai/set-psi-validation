---
name: psi-validation-report-generator
description: Exports validation results and metrics for the static documentation dashboard.
---

# PSI Validation Report Generator Skill

## When to Use

Use this skill when finalizing the daily or weekly validation cycle to export performance metrics to the documentation dashboard (GitHub Pages).

## Core Concepts

- **Static Export**: Generates JSON/Markdown artifacts compatible with the static site generator.
- **Reporting Consistency**: Updates `catalog.json` and associated documentation files in `docs/` to maintain the historical record.

## Quick Start

```bash
uv run scripts/python/jsonld_enricher.py --export-dashboard
```
