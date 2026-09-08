"""POC script to test Finnhub API for Thai and global stocks.

Evaluates quote, candle, and metric endpoints using the free tier API key.
"""

import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"
TIMEOUT = 10.0
HTTP_OK = 200
MIN_KEY_LEN = 8


def check_api_key() -> str:
    """Validate presence of Finnhub API key."""
    if not API_KEY:
        print("[ERROR] FINNHUB_API_KEY not found in .env")
        sys.exit(1)
    masked = API_KEY[:4] + "..." + API_KEY[-4:] if len(API_KEY) > MIN_KEY_LEN else "***"
    print(f"[INFO] Using Finnhub API Key: {masked}")
    return API_KEY


def run_test_quote(client: httpx.Client, symbol: str) -> dict | None:
    """Test /quote endpoint (Open, High, Low, Current Price, Previous Close)."""
    url = f"{BASE_URL}/quote"
    params: dict[str, str | int] = {"symbol": symbol, "token": API_KEY or ""}
    try:
        resp = client.get(url, params=params)
    except httpx.HTTPError as e:
        print(f"  [ERROR] Quote {symbol:10s} -> Request error: {e}")
        return None

    if resp.status_code == HTTP_OK:
        data = resp.json()
        c = data.get("c", 0)
        if c != 0:
            print(
                f"  [PASS] Quote {symbol:10s} -> "
                f"Price: {c}, Open: {data.get('o')}, PrevClose: {data.get('pc')}",
            )
            return data
        print(
            f"  [WARN] Quote {symbol:10s} -> "
            f"Returned zeros (unsupported/no live data on free tier): {data}",
        )
        return None

    print(f"  [FAIL] Quote {symbol:10s} -> HTTP {resp.status_code}: {resp.text}")
    return None


def run_test_candle(client: httpx.Client, symbol: str) -> dict | None:
    """Test /stock/candle endpoint (Daily EOD bar)."""
    url = f"{BASE_URL}/stock/candle"
    now = int(time.time())
    start = now - (7 * 86400)
    params: dict[str, str | int] = {
        "symbol": symbol,
        "resolution": "D",
        "from": start,
        "to": now,
        "token": API_KEY or "",
    }
    try:
        resp = client.get(url, params=params)
    except httpx.HTTPError as e:
        print(f"  [ERROR] Candle {symbol:10s} -> Request error: {e}")
        return None

    if resp.status_code == HTTP_OK:
        data = resp.json()
        status = data.get("s")
        if status == "ok":
            bars = len(data.get("c", []))
            print(f"  [PASS] Candle {symbol:10s} -> Found {bars} daily bars (status: ok)")
            return data
        print(f"  [WARN] Candle {symbol:10s} -> Status: '{status}' (no_data / unsupported)")
        return None

    print(f"  [FAIL] Candle {symbol:10s} -> HTTP {resp.status_code}: {resp.text}")
    return None


def run_test_basic_financials(client: httpx.Client, symbol: str) -> dict | None:
    """Test /stock/metric endpoint (P/E, Beta, 52-week High/Low)."""
    url = f"{BASE_URL}/stock/metric"
    params: dict[str, str | int] = {
        "symbol": symbol,
        "metric": "all",
        "token": API_KEY or "",
    }
    try:
        resp = client.get(url, params=params)
    except httpx.HTTPError as e:
        print(f"  [ERROR] Metric {symbol:10s} -> Request error: {e}")
        return None

    if resp.status_code == HTTP_OK:
        data = resp.json()
        metric = data.get("metric", {})
        if metric:
            pe = metric.get("peNormalizedAnnual") or metric.get("peExclExtraTTM")
            beta = metric.get("beta")
            print(
                f"  [PASS] Metric {symbol:10s} -> "
                f"PE: {pe}, Beta: {beta}, Metric count: {len(metric)}",
            )
            return metric
        print(f"  [WARN] Metric {symbol:10s} -> Empty metrics returned")
        return None

    print(f"  [FAIL] Metric {symbol:10s} -> HTTP {resp.status_code}: {resp.text}")
    return None


def main() -> None:
    """Run Finnhub POC test suite."""
    print("=" * 60)
    print("Finnhub API Test POC (SET vs US Stocks)")
    print("=" * 60)
    check_api_key()

    test_symbols = [
        ("AAPL", "US Baseline (Control)"),
        ("PTT.BK", "Thai Stock (.BK)"),
        ("DELTA.BK", "Thai Stock (.BK)"),
        ("PTT", "Thai Stock (Without suffix)"),
    ]

    with httpx.Client(timeout=TIMEOUT) as client:
        print("\n--- 1. Testing Live / EOD Quote Endpoint (/quote) ---")
        for sym, desc in test_symbols:
            print(f"Testing {sym} ({desc}):")
            run_test_quote(client, sym)

        print("\n--- 2. Testing Daily Candle / History Endpoint (/stock/candle) ---")
        for sym, desc in test_symbols:
            print(f"Testing {sym} ({desc}):")
            run_test_candle(client, sym)

        print("\n--- 3. Testing Financial Metrics Endpoint (/stock/metric) ---")
        for sym, desc in test_symbols[:2]:
            print(f"Testing {sym} ({desc}):")
            run_test_basic_financials(client, sym)

    print("\n" + "=" * 60)
    print("POC Test Completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
