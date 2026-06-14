---
name: setsmart-integration-complete
description: capture_market.py now fetches live SET Index data from SETSMART API instead of manual inputs
type: project
---

# SETSMART API Integration Complete

## Work Done

1. **capture_market.py** — added SETSMART API integration:
   - `fetch_setsmart_eod(symbol, date)` — calls `GET /api/listed-company-api/eod-price-by-symbol` with `api-key` header
   - `extract_market_prices(eod)` — maps EOD response (open, close, high, low) to ATO/ATC/volatility
   - `--symbol` CLI flag — when provided, fetches live data instead of requiring `--ato-price`/`--atc-price`/`--volatility`
   - Manual mode still works for backward compatibility
   - Added `httpx` to PEP 723 inline dependencies

2. **Workflow updated** — ATO/ATC steps now use `--symbol ${{ vars.SET_INDEX_SYMBOL || 'SET' }}` with `SETSMART_API_KEY` secret

3. **Secrets simplified** — from 6 secrets to 4:
   - Removed: `SET_ATO_PRICE`, `SET_ATC_PRICE`, `SET_VOLATILITY`
   - Added: `SETSMART_API_KEY`
   - New variable: `SET_INDEX_SYMBOL` (default: `SET`)

4. **Runbook updated** — `docs/01_runbook/001-github-setup-v01.md` reflects new secrets/variables

## Key Files

- `scripts/python/capture_market.py`
- `.github/workflows/intraday-pipeline.yml`
- `.env`
- `docs/01_runbook/001-github-setup-v01.md`

## Why: Eliminate manual price inputs — pipeline now auto-fetches real SET Index open/close/volatility from SETSMART.
