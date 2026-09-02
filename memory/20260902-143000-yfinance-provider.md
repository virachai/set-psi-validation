---
name: yfinance-market-data-provider
description: Configured Yahoo Finance (yfinance) as the default primary provider for capturing SET index market data.
metadata:
  type: project
---

**Summary:**
- Added `yfinance` package dependency to `pyproject.toml`.
- Implemented `fetch_yahoo_quote` in `scripts/python/providers.py` supporting `^SET.BK`.
- Updated `scripts/python/capture_market.py` to support `--provider yahoo` and set `yahoo` as the default provider.
- Verified all unit tests pass successfully.

**Why:**
Finnhub API lacks direct coverage for Thai SET indices (`^SET.BK`), whereas Yahoo Finance provides accurate and reliable open/close/high/low data for SET index validation.

**How to apply:**
Run `uv run python scripts/python/capture_market.py --mode ato --symbol ^SET.BK` (defaults to Yahoo Finance provider).
