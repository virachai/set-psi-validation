# /// script
# dependencies = [
#   "requests",
#   "python-dotenv"
# ]
# ///
import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env
load_dotenv()

def fetch_market_data(symbol: str) -> Dict[str, Any]:
    """Fetches real-time quote data from Finnhub."""
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("FINNHUB_API_KEY not found in environment variables.")

    # Finnhub API endpoint for real-time quotes
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
    
    try:
        response = requests.get(url)
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
