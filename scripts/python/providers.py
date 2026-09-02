import os
import httpx
from typing import Optional, Dict, Any
import yfinance as yf


def fetch_finnhub_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetches real-time quote data from Finnhub."""
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("[ERROR] FINNHUB_API_KEY not found in environment variables.")
        return None

    # Finnhub API endpoint for real-time quotes
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            if data and data.get("c", 0) > 0:
                print(f"[FINNHUB] Successfully fetched live quote for {symbol}: c={data.get('c')}, o={data.get('o')}")
            return data
    except Exception as e:
        print(f"[ERROR] Error fetching Finnhub data: {e}")
        return None


def fetch_yahoo_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetches SET / Thai stock market data from Yahoo Finance (e.g. ^SET.BK)."""
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

        # Finnhub-compatible dictionary structure: c: close, o: open, h: high, l: low, pc: previous close
        pc_p = float(df.iloc[-2]["Close"]) if len(df) > 1 else open_p

        data = {
            "c": close_p,
            "o": open_p,
            "h": high_p,
            "l": low_p,
            "pc": pc_p,
            "source": "yfinance"
        }
        print(f"[YFINANCE] Successfully fetched for {symbol}: o={open_p}, c={close_p}, h={high_p}, l={low_p}")
        return data
    except Exception as e:
        print(f"[ERROR] Error fetching Yahoo Finance data for {symbol}: {e}")
        return None
