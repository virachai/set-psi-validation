"""Market data provider: Yahoo Finance (yfinance).

The provider returns a normalized quote dict {c, o, h, l, pc} so callers
(capture_market.py) can treat the data source uniformly.
"""

from datetime import UTC, datetime, time
from typing import Any

import yfinance as yf

ATO_BAR_ICT = time(10, 0)  # SET morning session open (RFC 019: ato = open of the 10:00 bar)


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
            "source_granularity": "daily_bar",
            "fetched_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        print(f"[ERROR] Error fetching Yahoo Finance data for {symbol}: {e}")
        return None

    fmt = f"o={open_p}, c={close_p}, h={high_p}, l={low_p}"
    print(f"[YFINANCE] Successfully fetched for {symbol}: {fmt}")
    return data


def fetch_yahoo_ato_open(symbol: str, date_str: str) -> float | None:
    """Return the open of the date's 10:00 ICT 30m bar — the ATO price.

    The daily bar's Open is not the ATO print (RFC 015/019), so the ATO is
    read from the intraday bar that the auction opens.
    """
    if symbol.upper() in ["SET", "^SET"]:
        symbol = "^SET.BK"

    try:
        bars = yf.Ticker(symbol).history(period="1d", interval="30m")
    except Exception as e:
        print(f"[ERROR] Error fetching Yahoo intraday bars for {symbol}: {e}")
        return None

    for ts, bar in bars.iterrows():
        if ts.date().isoformat() == date_str and ts.time() == ATO_BAR_ICT:
            return float(bar["Open"])
    print(f"[WARN] No 10:00 bar for {symbol} on {date_str} in Yahoo intraday data")
    return None
