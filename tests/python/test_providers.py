"""Tests for providers.py — Yahoo quote freshness metadata (RFC-001 ISS-09/ISS-10)."""

import pathlib
import sys
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from providers import fetch_yahoo_quote


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
