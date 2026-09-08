"""POC script to test fetching Thai individual stocks via yfinance.

Extracts EOD OHLCV data for representative SET stocks and computes basic day metrics.
"""

import time
from typing import Any

import yfinance as yf

# Sample Universe: Large-cap Thai stocks across key sectors
SAMPLE_TICKERS = [
    "PTT.BK",  # Energy
    "DELTA.BK",  # Tech / Electronics
    "AOT.BK",  # Transportation
    "CPALL.BK",  # Commerce
    "KBANK.BK",  # Banking
]

REQUEST_DELAY_SEC = 1.0
THRESHOLD_PCT = 0.3


def fetch_stock_eod(ticker_symbol: str) -> dict[str, Any] | None:
    """Fetch recent EOD data for a single Thai stock and compute basic day metrics."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="5d", auto_adjust=False)

        if hist.empty:
            print(f"  [WARN] {ticker_symbol:10s} -> No historical data returned.")
            return None

        latest_bar = hist.iloc[-1]
        trade_date = str(latest_bar.name.date())
        open_price = float(latest_bar["Open"])
        high_price = float(latest_bar["High"])
        low_price = float(latest_bar["Low"])
        close_price = float(latest_bar["Close"])
        volume = int(latest_bar["Volume"])

        # Intraday return (Open to Close) & Day return (vs Prev Close if available)
        intraday_return_pct = (
            ((close_price - open_price) / open_price) * 100 if open_price > 0 else 0.0
        )
        day_range_pct = ((high_price - low_price) / open_price) * 100 if open_price > 0 else 0.0

        direction = (
            "UP"
            if intraday_return_pct > THRESHOLD_PCT
            else ("DOWN" if intraday_return_pct < -THRESHOLD_PCT else "FLAT")
        )

        result = {
            "symbol": ticker_symbol,
            "date": trade_date,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume,
            "intraday_ret_%": round(intraday_return_pct, 2),
            "range_%": round(day_range_pct, 2),
            "direction": direction,
        }

        print(
            f"  [PASS] {ticker_symbol:10s} | Date: {trade_date} | "
            f"O: {open_price:6.2f} | H: {high_price:6.2f} | L: {low_price:6.2f} | "
            f"C: {close_price:6.2f} | Intraday: {intraday_return_pct:+5.2f}% ({direction})",
        )
    except Exception as exc:
        print(f"  [ERROR] {ticker_symbol:10s} -> Failed: {exc}")
        return None
    else:
        return result


def main() -> None:
    """Run yfinance Thai stocks batch test."""
    print("=" * 75)
    print("Testing yfinance EOD Data Extraction for Thai Stocks (SET)")
    print("=" * 75)

    success_count = 0
    results: list[dict[str, Any]] = []

    for i, sym in enumerate(SAMPLE_TICKERS):
        res = fetch_stock_eod(sym)
        if res:
            success_count += 1
            results.append(res)

        # Politeness delay to prevent rate-limiting on GitHub Actions / CI
        if i < len(SAMPLE_TICKERS) - 1:
            time.sleep(REQUEST_DELAY_SEC)

    print("\n" + "-" * 75)
    print(f"Summary: Successfully fetched {success_count}/{len(SAMPLE_TICKERS)} stocks")
    print("-" * 75)


if __name__ == "__main__":
    main()
