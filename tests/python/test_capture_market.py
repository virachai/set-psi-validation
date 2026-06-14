"""Tests for capture_market.py — ATO/ATC capture, regime derivation, output."""

import json
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from capture_market import (
    derive_actual_regime,
    handle_ato,
    handle_atc,
    VALID_REGIMES,
    REGIME_TAXONOMY_URL,
)

# --- derive_actual_regime (double-check parity with validation_engine) ---


class TestDeriveActualRegime:
    THRESHOLD = 0.02

    def test_bullish(self):
        assert derive_actual_regime(100.0, 101.0, 0.01, self.THRESHOLD) == "Bullish"

    def test_bearish(self):
        assert derive_actual_regime(100.0, 99.0, 0.01, self.THRESHOLD) == "Bearish"

    def test_sideways(self):
        assert derive_actual_regime(100.0, 100.2, 0.01, self.THRESHOLD) == "Sideways"

    def test_risk_off(self):
        assert derive_actual_regime(100.0, 99.0, 0.03, self.THRESHOLD) == "Risk-Off"

    def test_crisis(self):
        assert derive_actual_regime(100.0, 97.5, 0.05, self.THRESHOLD) == "Crisis"

    def test_unclassified(self):
        assert derive_actual_regime(100.0, 101.0, 0.03, self.THRESHOLD) == "Unclassified"


# --- handle_ato ---


class TestHandleAto:
    def test_output_structure(self):
        result = handle_ato("2026-06-14", 1450.20)

        assert result["@context"] == "https://schema.org"
        assert result["@type"] == "Observation"
        assert "observationDate" in result

        # measuredProperty points to taxonomy
        assert result["measuredProperty"]["@type"] == "DefinedTerm"
        assert result["measuredProperty"]["inDefinedTermSet"] == REGIME_TAXONOMY_URL

        # variableMeasured has ATO price
        measures = {m["name"]: m["value"] for m in result["variableMeasured"]}
        assert measures["ATO Price"] == 1450.20

        # Backward-compat fields
        assert result["date"] == "2026-06-14"
        assert result["atoPrice"] == 1450.20
        assert result["status"] == "partial"

    def test_ato_price_zero(self):
        result = handle_ato("2026-06-14", 0.0)
        measures = {m["name"]: m["value"] for m in result["variableMeasured"]}
        assert measures["ATO Price"] == 0.0

    def test_schema_org_compliant(self):
        """Verify all required schema.org Observation fields are present."""
        result = handle_ato("2026-06-14", 1500.0)
        assert "@context" in result
        assert "@type" in result
        assert "name" in result
        assert "observationDate" in result
        assert "measuredProperty" in result
        assert "variableMeasured" in result


# --- handle_atc ---


class TestHandleAtc:
    def test_complete_output_structure(self, tmp_path, monkeypatch):
        """Full ATC record with no prior ATO (fallback)."""
        monkeypatch.chdir(tmp_path)

        result = handle_atc("2026-06-14", 1438.10, 1.95, 0.02)

        assert result["@type"] == "Observation"
        assert result["status"] == "complete"
        assert "observationPeriod" in result

        measures = {m["name"]: m["value"] for m in result["variableMeasured"]}
        assert "ATO Price" in measures
        assert "ATC Price" in measures
        assert "Return %" in measures
        assert "Intraday Volatility" in measures
        assert "Actual Regime" in measures

        # Backward-compat fields
        assert result["atcPrice"] == 1438.10
        assert result["volatilityIndex"] == 1.95

    def test_regime_in_valid_list(self, tmp_path, monkeypatch):
        """ActualRegime value must be in VALID_REGIMES or Unclassified."""
        monkeypatch.chdir(tmp_path)
        regimes_seen = set()

        # Bullish
        r = handle_atc("2026-06-01", 101.0, 0.01, 0.02)
        regimes_seen.add(r["actualRegime"])

        # Bearish
        r = handle_atc("2026-06-02", 99.0, 0.01, 0.02)
        regimes_seen.add(r["actualRegime"])

        # Risk-Off
        r = handle_atc("2026-06-03", 99.0, 0.03, 0.02)
        regimes_seen.add(r["actualRegime"])

        for regime in regimes_seen:
            assert regime in VALID_REGIMES or regime == "Unclassified"

    def test_return_pct_calculation(self, tmp_path, monkeypatch):
        """Verify return % is computed correctly."""
        monkeypatch.chdir(tmp_path)

        # Create existing ATO file
        ato_file = tmp_path / "market-data" / "2026-06-14.json"
        ato_file.parent.mkdir()
        ato_file.write_text(json.dumps({"atoPrice": 100.0}))

        result = handle_atc("2026-06-14", 101.50, 0.01, 0.02)
        assert result["returnPct"] == 1.5  # (101.5 - 100) / 100 * 100
        assert result["atoPrice"] == 100.0
        assert result["atcPrice"] == 101.50

    def test_atc_fallback_no_ato(self, tmp_path, monkeypatch):
        """When no ATO file exists, ATC price is used as fallback ATO → 0% return."""
        monkeypatch.chdir(tmp_path)

        result = handle_atc("2026-06-14", 1450.0, 0.01, 0.02)
        assert result["atoPrice"] == 1450.0  # fallback to atc_price
        assert result["returnPct"] == 0.0

    @pytest.mark.parametrize(
        "ato, atc, vol, threshold, expected_regime",
        [
            (100.0, 101.0, 0.01, 0.02, "Bullish"),
            (100.0, 99.0, 0.01, 0.02, "Bearish"),
            (100.0, 100.1, 0.01, 0.02, "Sideways"),
            (100.0, 99.0, 0.03, 0.02, "Risk-Off"),
            (100.0, 97.5, 0.05, 0.02, "Crisis"),
        ],
    )
    def test_regime_derivation_integration(
        self, tmp_path, monkeypatch, ato, atc, vol, threshold, expected_regime
    ):
        """End-to-end: ATO file + handle_atc → correct regime."""
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        (mdir / "2026-06-14.json").write_text(json.dumps({"atoPrice": ato}))

        result = handle_atc("2026-06-14", atc, vol, threshold)
        assert result["actualRegime"] == expected_regime
