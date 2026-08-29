import os
import httpx
from typing import Optional, Dict, Any


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
            return response.json()
    except Exception as e:
        print(f"[ERROR] Error fetching Finnhub data: {e}")
        return None
