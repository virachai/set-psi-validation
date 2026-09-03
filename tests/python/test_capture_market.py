"""Tests for capture_market.py — ATO/ATC capture, regime derivation, output."""

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from capture_market import (
    REGIME_TAXONOMY_URL,
    THRESHOLD_MIN_HISTORY_DAYS,
    VALID_REGIMES,
    _fetch_live_prices,
    compute_rolling_threshold_mean,
    extract_market_prices,
    handle_atc,
    handle_ato,
    handle_noon,
    handle_pmopen,
    load_existing,
)
from regime_rules import DEFAULT_THRESHOLD_MEAN, derive_actual_regime

# --- extract_market_prices ---


class TestExtractMarketPrices:
    def test_normal_prices(self):
        eod = {"open": 100.0, "close": 105.0, "high": 110.0, "low": 95.0}
        ato, atc, vol = extract_market_prices(eod)
        assert ato == 100.0
        assert atc == 105.0
        assert vol == 0.05  # (110-95)/100 = 0.15, capped at 0.05

    def test_open_price_zero(self):
        """Should not raise DivisionByZero, should return default volatility."""
        eod = {"open": 0.0, "close": 105.0, "high": 110.0, "low": 95.0}
        ato, atc, vol = extract_market_prices(eod)
        assert ato == 0.0
        assert atc == 105.0
        assert vol == 0.05  # (110-95) / 102.5 = 0.146, capped at 0.05

    def test_alternate_field_names(self):
        eod = {"openPrice": 100.0, "last": 102.0, "highPrice": 103.0, "lowPrice": 99.0}
        ato, atc, vol = extract_market_prices(eod)
        assert ato == 100.0
        assert atc == 102.0
        assert vol == 0.0396  # (103-99) / 101 = 0.039603...


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
        ("ato", "atc", "vol", "threshold", "expected_regime"),
        [
            (100.0, 101.0, 0.01, 0.02, "Bullish"),
            (100.0, 99.0, 0.01, 0.02, "Bearish"),
            (100.0, 100.1, 0.01, 0.02, "Sideways"),
            (100.0, 99.0, 0.03, 0.02, "Risk-Off"),
            (100.0, 97.5, 0.05, 0.02, "Crisis"),
        ],
    )
    def test_regime_derivation_integration(
        self,
        tmp_path,
        monkeypatch,
        ato: float,
        atc: float,
        vol: float,
        threshold: float,
        expected_regime: str,
    ) -> None:
        """End-to-end: ATO file + handle_atc → correct regime."""
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        (mdir / "2026-06-14.json").write_text(json.dumps({"atoPrice": ato}))

        result = handle_atc("2026-06-14", atc, vol, threshold)
        assert result["actualRegime"] == expected_regime

    def test_load_existing_prefers_ato_file(self, tmp_path, monkeypatch):
        """Ensure load_existing properly extracts atoPrice from *-ato.json when both exist."""
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        ato_payload = {"atoPrice": 1550.0, "status": "partial"}
        atc_payload = {"atcPrice": 1540.0, "status": "complete"}
        (mdir / "2026-06-14-100000-ato.json").write_text(json.dumps(ato_payload))
        (mdir / "2026-06-14-163000-atc.json").write_text(json.dumps(atc_payload))

        loaded = load_existing("2026-06-14")
        assert loaded.get("atoPrice") == 1550.0

    def test_fetch_live_prices_fails_closed(self, monkeypatch):
        """Ensure _fetch_live_prices raises RuntimeError if provider returns no data."""
        # Finnhub returning empty
        monkeypatch.setattr("capture_market.fetch_finnhub_quote", lambda sym: {})
        with pytest.raises(RuntimeError, match="Finnhub API returned no valid quote"):
            _fetch_live_prices("finnhub", "SET", "2026-06-14", "atc")

        # Yahoo returning empty
        monkeypatch.setattr("capture_market.fetch_yahoo_quote", lambda sym: {})
        with pytest.raises(RuntimeError, match="Yahoo Finance returned no valid quote"):
            _fetch_live_prices("yahoo", "^SET.BK", "2026-06-14", "atc")

        # SETSMART returning None
        monkeypatch.setattr("capture_market.fetch_setsmart_eod", lambda sym, dt: None)
        with pytest.raises(RuntimeError, match="SETSMART API returned no data"):
            _fetch_live_prices("setsmart", "SET", "2026-06-14", "atc")


class TestHandleNoon:
    """Morning-session close (ATO -> Noon) capture — used to score `am` predictions."""

    def test_complete_output_structure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        (mdir / "2026-06-14-100000-ato.json").write_text(
            json.dumps({"atoPrice": 100.0, "status": "partial"}),
        )

        result = handle_noon("2026-06-14", 101.0, 0.01, 0.02)

        assert result["window"] == "morning"
        assert result["status"] == "complete"
        assert result["atoPrice"] == 100.0
        assert result["noonPrice"] == 101.0
        assert result["returnPct"] == 1.0
        assert result["actualRegime"] == "Bullish"

        measures = {m["name"]: m["value"] for m in result["variableMeasured"]}
        assert measures["Noon Price"] == 101.0
        assert measures["Morning Return %"] == 1.0

    def test_fallback_no_ato(self, tmp_path, monkeypatch):
        """When no ATO file exists, noon price is used as fallback ATO -> 0% return."""
        monkeypatch.chdir(tmp_path)
        result = handle_noon("2026-06-14", 1450.0, 0.01, 0.02)
        assert result["atoPrice"] == 1450.0
        assert result["returnPct"] == 0.0

    def test_actual_regime_reuses_same_field_name_as_atc(self, tmp_path, monkeypatch):
        """The noon record must expose 'actualRegime' the same way the atc record
        does, so validation_engine's generic regime extraction works on either
        file unchanged."""
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        (mdir / "2026-06-14-100000-ato.json").write_text(json.dumps({"atoPrice": 100.0}))
        noon_result = handle_noon("2026-06-14", 100.05, 0.01, 0.02)
        atc_result = handle_atc("2026-06-14", 100.05, 0.01, 0.02)
        assert noon_result["actualRegime"] == atc_result["actualRegime"] == "Sideways"


class TestHandlePmopen:
    """Afternoon-session open (partial) capture — awaits ATC to derive the afternoon window."""

    def test_output_structure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = handle_pmopen("2026-06-14", 1445.0)
        assert result["window"] == "afternoon"
        assert result["status"] == "partial"
        assert result["pmOpenPrice"] == 1445.0
        measures = {m["name"]: m["value"] for m in result["variableMeasured"]}
        assert measures["PM Open Price"] == 1445.0


class TestHandleAtcAfternoonWindow:
    """handle_atc must also derive the PM Open -> ATC window when a pmopen record exists."""

    def test_no_pmopen_record_omits_afternoon_fields(self, tmp_path, monkeypatch):
        """Backward compatibility: without a pmopen capture, afternoon fields are None
        and no 'Afternoon Actual Regime' entry appears in variableMeasured."""
        monkeypatch.chdir(tmp_path)
        result = handle_atc("2026-06-14", 1438.10, 0.01, 0.02)
        assert result["pmOpenPrice"] is None
        assert result["afternoonReturnPct"] is None
        assert result["afternoonRegime"] is None
        names = {m["name"] for m in result["variableMeasured"]}
        assert "Afternoon Actual Regime" not in names

    def test_with_pmopen_record_derives_afternoon_window(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        (mdir / "2026-06-14-100000-ato.json").write_text(json.dumps({"atoPrice": 100.0}))
        (mdir / "2026-06-14-143000-pmopen.json").write_text(
            json.dumps({"pmOpenPrice": 100.0, "status": "partial"}),
        )

        result = handle_atc("2026-06-14", 101.0, 0.01, 0.02)

        assert result["pmOpenPrice"] == 100.0
        assert result["afternoonReturnPct"] == 1.0
        assert result["afternoonRegime"] == "Bullish"
        # Full-day regime (ato 100.0 -> atc 101.0) computed independently too.
        assert result["actualRegime"] == "Bullish"

        measures = {m["name"]: m["value"] for m in result["variableMeasured"]}
        assert measures["Afternoon Actual Regime"] == "Bullish"
        assert measures["Afternoon Return %"] == 1.0


class TestComputeRollingThresholdMean:
    """Cover the adaptive volatility threshold (replaces the old hardcoded 0.02)."""

    def _write_atc(self, mdir: pathlib.Path, date: str, volatility: float) -> None:
        payload = {"status": "complete", "volatilityIndex": volatility}
        (mdir / f"{date}-163000-atc.json").write_text(json.dumps(payload))

    def test_no_history_falls_back_to_default(self, tmp_path, monkeypatch):
        """Cold start (no market-data dir yet): use the static default, not crash."""
        monkeypatch.chdir(tmp_path)
        assert compute_rolling_threshold_mean("2026-06-14") == DEFAULT_THRESHOLD_MEAN

    def test_below_minimum_history_falls_back_to_default(self, tmp_path, monkeypatch):
        """Fewer than THRESHOLD_MIN_HISTORY_DAYS prior days: too noisy, use default."""
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        for i in range(THRESHOLD_MIN_HISTORY_DAYS - 1):
            self._write_atc(mdir, f"2026-06-{10 + i:02d}", 0.05)

        assert compute_rolling_threshold_mean("2026-06-20") == DEFAULT_THRESHOLD_MEAN

    def test_averages_prior_days_once_enough_history(self, tmp_path, monkeypatch):
        """With enough history, the mean of prior volatilityIndex values is used."""
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        volatilities = [0.01, 0.02, 0.03, 0.04, 0.05]
        for i, vol in enumerate(volatilities):
            self._write_atc(mdir, f"2026-06-{10 + i:02d}", vol)

        result = compute_rolling_threshold_mean("2026-06-20")
        assert result == pytest.approx(sum(volatilities) / len(volatilities))

    def test_excludes_current_and_future_dates(self, tmp_path, monkeypatch):
        """No lookahead: today's own file (if present) and later dates must not count."""
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        for i in range(THRESHOLD_MIN_HISTORY_DAYS):
            self._write_atc(mdir, f"2026-06-{10 + i:02d}", 0.01)
        # Same-day and future entries must be ignored even if present.
        self._write_atc(mdir, "2026-06-20", 0.99)
        self._write_atc(mdir, "2026-06-25", 0.99)

        result = compute_rolling_threshold_mean("2026-06-20")
        assert result == pytest.approx(0.01)

    def test_incomplete_or_missing_volatility_ignored(self, tmp_path, monkeypatch):
        """Partial (ATO-only) records and records missing volatilityIndex don't count."""
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        for i in range(THRESHOLD_MIN_HISTORY_DAYS):
            self._write_atc(mdir, f"2026-06-{10 + i:02d}", 0.02)
        (mdir / "2026-06-18-100000-ato.json").write_text(
            json.dumps({"status": "partial", "atoPrice": 1500.0}),
        )

        result = compute_rolling_threshold_mean("2026-06-20")
        assert result == pytest.approx(0.02)
