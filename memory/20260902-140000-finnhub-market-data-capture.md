---
name: finnhub-market-data-capture
description: Validated creation of market-data artifacts using Finnhub provider integration.
metadata:
  type: project
---

**Summary:**
Successfully created and captured market data files in `market-data/` using the Finnhub provider integration (`scripts/python/providers.py` & `capture_market.py`). Verified correct schema.org Observation structure and successful enrichment via `jsonld_enricher.py`.

**Why:**
Enables robust testing and capture of external market quotes using Finnhub when SETSMART is offline or unconfigured.

**How to apply:**
Run `uv run python scripts/python/capture_market.py --mode ato --symbol <symbol> --provider finnhub` followed by `uv run python scripts/python/jsonld_enricher.py`.
