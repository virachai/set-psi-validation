"""Integration tests: capture_market.py against a stubbed SETSMART API.

Verifies the request contract (URL, params, headers), the failure paths
(auth, empty payload, HTTP error, timeout), and the end-to-end pipeline
(fetch -> extract -> ATO -> ATC -> regime derivation -> persisted file)
with output schema assertions (schema.org Observation JSON-LD).
"""

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts" / "python"))

import capture_market
from capture_market import (
    REGIME_TAXONOMY_URL,
    VALID_REGIMES,
    extract_market_prices,
    fetch_setsmart_eod,
    handle_atc,
    handle_ato,
)

EOD_PAYLOAD = {
    "symbol": "SET",
    "open": 1500.0,
    "close": 1510.0,
    "high": 1520.0,
    "low": 1490.0,
}


class TestSetsmartRequestContract:
    """Stub the API and verify the request we send matches the SETSMART contract."""

    @pytest.fixture
    def set_api_key(self, monkeypatch):
        monkeypatch.setattr(capture_market, "SETSMART_API_KEY", "test-api-key")

    def test_fetch_success(self, set_api_key):
        def handler(request):
            assert request.url.path.endswith("/eod-price-by-symbol")
            assert request.url.params["symbol"] == "SET"
            assert request.url.params["startDate"] == "2026-08-28"
            assert request.url.params["endDate"] == "2026-08-28"
            assert request.url.params["adjustedPriceFlag"] == "N"
            assert request.headers["api-key"] == "test-api-key"
            assert request.headers["Accept"] == "application/json"
            return httpx.Response(200, json=[EOD_PAYLOAD])

        transport = httpx.MockTransport(handler)
        result = fetch_setsmart_eod("SET", "2026-08-28", transport=transport)
        assert result == EOD_PAYLOAD

    def test_auth_failure_returns_none(self, set_api_key):
        transport = httpx.MockTransport(
            lambda r: httpx.Response(401, json={"error": "unauthorized"}),
        )
        assert fetch_setsmart_eod("SET", "2026-08-28", transport=transport) is None

    def test_http_error_returns_none(self, set_api_key):
        transport = httpx.MockTransport(lambda r: httpx.Response(500, json={}))
        assert fetch_setsmart_eod("SET", "2026-08-28", transport=transport) is None

    def test_empty_payload_returns_none(self, set_api_key):
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
        assert fetch_setsmart_eod("SET", "2026-08-28", transport=transport) is None

    def test_timeout_returns_none(self, set_api_key):
        def handler(request):
            exc_msg = "simulated timeout"
            raise httpx.ReadTimeout(exc_msg)

        transport = httpx.MockTransport(handler)
        assert fetch_setsmart_eod("SET", "2026-08-28", transport=transport) is None

    def test_missing_api_key_returns_none(self, monkeypatch):
        monkeypatch.setattr(capture_market, "SETSMART_API_KEY", None)
        assert fetch_setsmart_eod("SET", "2026-08-28") is None


class TestFullPipelineAgainstStub:
    """End-to-end: stubbed API -> ATO -> ATC -> persisted schema.org file."""

    def test_ato_atc_cycle_produces_valid_observation(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(capture_market, "SETSMART_API_KEY", "test-api-key")

        transport = httpx.MockTransport(lambda r: httpx.Response(200, json=[EOD_PAYLOAD]))

        # Fetch and extract, as the script's main() does
        eod = fetch_setsmart_eod("SET", "2026-08-28", transport=transport)
        assert eod is not None
        ato_price, atc_price, volatility = extract_market_prices(eod)
        assert ato_price == 1500.0
        assert atc_price == 1510.0

        # ATO capture -> file
        ato_record = handle_ato("2026-08-28", ato_price)
        capture_market.save_market_data(ato_record, "2026-08-28", "ato")

        # ATC capture merges the ATO file and derives the regime
        atc_record = handle_atc("2026-08-28", atc_price, volatility, threshold_mean=0.02)
        filepath = capture_market.save_market_data(atc_record, "2026-08-28", "atc")

        # --- Output schema assertions (schema.org Observation JSON-LD) ---
        assert atc_record["@context"] == "https://schema.org"
        assert atc_record["@type"] == "Observation"
        assert atc_record["observationDate"] == "2026-08-28"
        assert "observationPeriod" in atc_record

        measured = atc_record["measuredProperty"]
        assert measured["@type"] == "DefinedTerm"
        assert measured["name"] == "Actual Regime"
        assert measured["inDefinedTermSet"] == REGIME_TAXONOMY_URL

        measures = {m["name"]: m["value"] for m in atc_record["variableMeasured"]}
        assert set(measures) == {
            "ATO Price",
            "ATC Price",
            "Return %",
            "Intraday Volatility",
            "Actual Regime",
        }
        assert measures["ATO Price"] == 1500.0
        assert measures["ATC Price"] == 1510.0
        assert measures["Return %"] == pytest.approx(0.67)
        assert measures["Actual Regime"] == "Bullish"

        # Backward-compat fields
        assert atc_record["status"] == "complete"
        assert (
            atc_record["actualRegime"] in VALID_REGIMES
            or atc_record["actualRegime"] == "Unclassified"
        )

        # Persisted file round-trips
        with Path(filepath).open(encoding="utf-8") as f:
            assert json.load(f) == atc_record
