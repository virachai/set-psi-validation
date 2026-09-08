---
name: finnhub-vs-yfinance-thai-stock-poc
description: Evaluated Finnhub and yfinance APIs for Thai stock prediction validation; Finnhub returns 403 on free tier while yfinance successfully extracts SET EOD data.
metadata:
  pinned: false
---

# Finnhub vs yfinance for Thai Stock EOD Validation POC

## 1. Context & Objective
Evaluated feasibility of using GitHub Actions to predict individual Thai stocks in the morning and validate against actual market close prices in the evening without real-time streaming requirements.

## 2. Findings & Empirical Test Results
- **Finnhub API (`scripts/poc/test_finnhub.py`)**:
  - US Stock baseline (`AAPL`): Succeeded on `/quote` (price returned) and `/stock/metric` (133 financial metrics).
  - Thai Stocks (`PTT.BK`, `DELTA.BK`): Failed with `HTTP 403 Forbidden: {"error":"You don't have access to this resource."}` across `/quote`, `/stock/candle`, and `/stock/metric`. Non-US / SET market data is restricted to paid institutional tiers.
- **yfinance (`scripts/poc/test_yfinance_set.py`)**:
  - Successfully retrieved 5/5 sample SET stocks (`PTT.BK`, `DELTA.BK`, `AOT.BK`, `CPALL.BK`, `KBANK.BK`).
  - Extracted full EOD OHLCV bars and derived intraday return (`(Close - Open) / Open`) and direction (`UP`, `DOWN`, `FLAT`).

## 3. Decision & Recommended Architecture
- **Provider Choice**: Reject Finnhub for SET individual stock validation due to API tier barrier; adopt `yfinance` for EOD batch processing.
- **GitHub Actions Execution**:
  - Morning (08:30-09:30 ICT): Generate and persist stock predictions to immutable JSONL.
  - Evening (17:30-18:30 ICT): Batch-fetch EOD actual prices via `yfinance` with a 1.0s request delay to avoid IP throttling, followed by directional and return validation.
