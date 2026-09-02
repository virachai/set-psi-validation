"""Fetch a real-time Finnhub quote (standalone requests-based sample).

The pipeline uses providers.py (httpx/yfinance) instead; this script remains
a standalone demonstration of the raw Finnhub endpoint.
"""

import os
from typing import Any

import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

REQUEST_TIMEOUT = 10.0


def fetch_market_data(symbol: str) -> dict[str, Any]:
    """Fetch a real-time quote from the Finnhub API."""
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        msg = "FINNHUB_API_KEY not found in environment variables."
        raise ValueError(msg)

    # Finnhub API endpoint for real-time quotes
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return {}


if __name__ == "__main__":
    # Example usage: Fetching a symbol (e.g., 'AAPL')
    symbol_to_fetch = "AAPL"
    data = fetch_market_data(symbol_to_fetch)
    print(f"Market data for {symbol_to_fetch}: {data}")
