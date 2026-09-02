"""Market data providers: Finnhub REST API and Yahoo Finance (yfinance).

Both providers return a normalized quote dict {c, o, h, l, pc} so callers
(capture_market.py) can treat the data source uniformly.
"""

import os
from typing import Any

import httpx
import yfinance as yf

DEFAULT_TIMEOUT = 30.0


def fetch_finnhub_quote(symbol: str) -> dict[str, Any] | None:
    """Fetch a real-time quote from the Finnhub API."""
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("[ERROR] FINNHUB_API_KEY not found in environment variables.")
        return None

    # Finnhub API endpoint for real-time quotes
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            if data and data.get("c", 0) > 0:
                quote = data.get("c")
                open_p = data.get("o")
                msg = (
                    f"[FINNHUB] Successfully fetched live quote for {symbol}: "
                    f"c={quote}, o={open_p}"
                )
                print(msg)
            return data
    except Exception as e:
        print(f"[ERROR] Error fetching Finnhub data: {e}")
        return None


def fetch_yahoo_quote(symbol: str) -> dict[str, Any] | None:
    """Fetch SET / Thai stock market data from Yahoo Finance (e.g. ^SET.BK)."""
    # Normalize common aliases
    if symbol.upper() in ["SET", "^SET"]:
        symbol = "^SET.BK"

    try:
        print(f"[YFINANCE] Fetching quote for {symbol}...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2d")
        if df.empty:
            print(f"[WARN] No data returned from Yahoo Finance for {symbol}")
            return None

        latest = df.iloc[-1]
        open_p = float(latest["Open"])
        close_p = float(latest["Close"])
        high_p = float(latest["High"])
        low_p = float(latest["Low"])

        pc_p = float(df.iloc[-2]["Close"]) if len(df) > 1 else open_p

        data = {
            "c": close_p,
            "o": open_p,
            "h": high_p,
            "l": low_p,
            "pc": pc_p,
            "source": "yfinance",
        }
    except Exception as e:
        print(f"[ERROR] Error fetching Yahoo Finance data for {symbol}: {e}")
        return None

    fmt = f"o={open_p}, c={close_p}, h={high_p}, l={low_p}"
    print(f"[YFINANCE] Successfully fetched for {symbol}: {fmt}")
    return data
