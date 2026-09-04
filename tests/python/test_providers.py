"""Tests for providers.py — Finnhub/Yahoo quote freshness metadata (RFC-001 ISS-09/ISS-10)."""

import pathlib
import sys
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from providers import fetch_finnhub_quote, fetch_yahoo_quote


class TestFetchFinnhubQuote:
    def test_attaches_fetched_at(self, monkeypatch):
        monkeypatch.setenv("FINNHUB_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"c": 1450.0, "o": 1440.0}
        mock_response.raise_for_status.return_value = None
        with patch("httpx.Client.get", return_value=mock_response):
            data = fetch_finnhub_quote("SET")
        assert "fetched_at" in data


class TestFetchYahooQuote:
    def test_attaches_freshness_and_granularity(self, monkeypatch):
        df = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "Close": [101.0, 102.0],
                "High": [102.0, 103.0],
                "Low": [99.0, 100.0],
            },
        )
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df
        with patch("yfinance.Ticker", return_value=mock_ticker):
            data = fetch_yahoo_quote("^SET.BK")

        assert data["source_granularity"] == "daily_bar"
        assert "fetched_at" in data
