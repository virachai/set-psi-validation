"""Tests for capture_market.py — single-cycle ATC capture, regime derivation, output."""

import json
import pathlib
import sys
from datetime import UTC, datetime, time

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from capture_market import (
    SET_MARKET_CLOSE_ICT,
    THRESHOLD_MIN_HISTORY_DAYS,
    VALID_REGIMES,
    _already_captured,
    _assert_after_open,
    _assert_before_cutoff,
    _assert_in_window,
    _fetch_live_prices,
    _mark_bypass,
    compute_rolling_threshold_mean,
    extract_market_prices,
    handle_atc,
    save_market_data,
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

    def test_open_price_zero_fails_closed(self):
        """A missing/zero open price must raise, not silently default to 0.0."""
        eod = {"open": 0.0, "close": 105.0, "high": 110.0, "low": 95.0}
        with pytest.raises(RuntimeError, match="Missing/invalid open price"):
            extract_market_prices(eod)

    def test_missing_high_fails_closed(self):
        eod = {"open": 100.0, "close": 105.0, "low": 95.0}
        with pytest.raises(RuntimeError, match="Missing/invalid high price"):
            extract_market_prices(eod)

    def test_missing_low_fails_closed(self):
        eod = {"open": 100.0, "close": 105.0, "high": 110.0}
        with pytest.raises(RuntimeError, match="Missing/invalid low price"):
            extract_market_prices(eod)

    def test_missing_close_fails_closed(self):
        eod = {"open": 100.0, "high": 110.0, "low": 95.0}
        with pytest.raises(RuntimeError, match="Missing/invalid close price"):
            extract_market_prices(eod)

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


# --- ---


class TestHandleAtc:
    def test_complete_output_structure(self):
        """Full ATC record built from ATO and ATC prices fetched in one call."""
        result = handle_atc("2026-06-14", 1420.0, 1438.10, 1.95, 0.02)

        assert result["@type"] == "Observation"
        assert result["status"] == "complete"
        assert result["observationPeriod"] == "2026-06-14T10:00:00+07:00/2026-06-14T16:30:00+07:00"

        measures = {m["name"]: m["value"] for m in result["variableMeasured"]}
        assert "ATO Price" in measures
        assert "ATC Price" in measures
        assert "Return %" in measures
        assert "Intraday Volatility" in measures
        assert "Actual Regime" in measures

        # Backward-compat fields
        assert result["atoPrice"] == 1420.0
        assert result["atcPrice"] == 1438.10
        assert result["volatilityIndex"] == 1.95

    def test_regime_in_valid_list(self):
        """ActualRegime value must be in VALID_REGIMES or Unclassified."""
        cases = [(101.0, 0.01), (99.0, 0.01), (99.0, 0.03)]  # Bullish, Bearish, Risk-Off
        for atc, vol in cases:
            regime = handle_atc("2026-06-01", 100.0, atc, vol, 0.02)["actualRegime"]
            assert regime in VALID_REGIMES or regime == "Unclassified"

    def test_return_pct_calculation(self):
        """Verify return % is computed correctly."""
        result = handle_atc("2026-06-14", 100.0, 101.50, 0.01, 0.02)
        assert result["returnPct"] == 1.5  # (101.5 - 100) / 100 * 100
        assert result["atoPrice"] == 100.0
        assert result["atcPrice"] == 101.50

    @pytest.mark.parametrize("ato", [0.0, -1.0, None])
    def test_atc_fails_closed_on_invalid_ato(self, ato, tmp_path, monkeypatch):
        """An invalid ATO price must fail closed, not fabricate a return."""
        monkeypatch.chdir(tmp_path)  # keep log_failure output out of the repo
        with pytest.raises(RuntimeError, match="Invalid ATO price"):
            handle_atc("2026-06-14", ato, 1450.0, 0.01, 0.02)

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
        ato: float,
        atc: float,
        vol: float,
        threshold: float,
        expected_regime: str,
    ) -> None:
        """End-to-end: ATO/ATC prices + handle_atc -> correct regime."""
        result = handle_atc("2026-06-14", ato, atc, vol, threshold)
        assert result["actualRegime"] == expected_regime

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

    def test_fetch_live_prices_fails_closed_on_missing_open(self, monkeypatch):
        """Finnhub/Yahoo quotes with a valid close but missing open must still fail closed."""
        monkeypatch.setattr(
            "capture_market.fetch_finnhub_quote",
            lambda sym: {"c": 1450.0, "o": 0.0},
        )
        with pytest.raises(RuntimeError, match="no valid open price"):
            _fetch_live_prices("finnhub", "SET", "2026-06-14", "atc")

        monkeypatch.setattr(
            "capture_market.fetch_yahoo_quote",
            lambda sym: {"c": 1450.0, "o": 0.0, "h": 1460.0, "l": 1440.0},
        )
        with pytest.raises(RuntimeError, match="no valid open price"):
            _fetch_live_prices("yahoo", "^SET.BK", "2026-06-14", "atc")

    def test_fetch_live_prices_fails_closed_on_missing_high_low(self, monkeypatch):
        """Yahoo quotes missing high/low must fail closed rather than default to open/close."""
        monkeypatch.setattr(
            "capture_market.fetch_yahoo_quote",
            lambda sym: {"c": 1450.0, "o": 1440.0, "h": 0.0, "l": 1430.0},
        )
        with pytest.raises(RuntimeError, match="no valid high/low price"):
            _fetch_live_prices("yahoo", "^SET.BK", "2026-06-14", "atc")


class TestAssertAfterOpen:
    """Fail-closed guard against a capture taken before its window opens."""

    def test_raises_before_open(self):
        with pytest.raises(RuntimeError, match="atc capture attempted"):
            _assert_after_open(
                "atc",
                SET_MARKET_CLOSE_ICT,
                datetime(2026, 6, 14, 16, 29, tzinfo=UTC),
            )

    def test_passes_at_boundary(self):
        _assert_after_open("atc", SET_MARKET_CLOSE_ICT, datetime(2026, 6, 14, 16, 30, tzinfo=UTC))

    def test_passes_after_open(self):
        _assert_after_open("atc", SET_MARKET_CLOSE_ICT, datetime(2026, 6, 14, 16, 31, tzinfo=UTC))


# (mode, too-early, in-window, too-late-or-None)
_WINDOW_CASES = [
    ("atc", time(16, 29), time(16, 45), None),
]


class TestAssertInWindow:
    """Each mode's capture is valid only inside its own ICT window."""

    @staticmethod
    def _at(t: time) -> datetime:
        return datetime(2026, 6, 15, t.hour, t.minute, tzinfo=UTC)

    @pytest.mark.parametrize(("mode", "early", "ok", "late"), _WINDOW_CASES)
    def test_window_boundaries(self, mode, early, ok, late):
        with pytest.raises(RuntimeError):
            _assert_in_window(mode, self._at(early))
        assert _assert_in_window(mode, self._at(ok)) is False
        if late is not None:
            with pytest.raises(RuntimeError):
                _assert_in_window(mode, self._at(late))

    def test_bypass_flag_downgrades_to_warning(self, monkeypatch):
        monkeypatch.setenv("PSI_BYPASS_WINDOW_GUARD", "true")
        assert _assert_in_window("atc", self._at(time(9, 28))) is True

    def test_bypass_flag_does_not_affect_in_window_capture(self, monkeypatch):
        monkeypatch.setenv("PSI_BYPASS_WINDOW_GUARD", "true")
        assert _assert_in_window("atc", self._at(time(16, 45))) is False


class TestMarkBypass:
    def test_stamps_only_when_bypassed(self):
        assert _mark_bypass({"a": 1}, bypassed=True)["windowGuardBypassed"] is True
        assert "windowGuardBypassed" not in _mark_bypass({"a": 1}, bypassed=False)


class TestAssertBeforeCutoff:
    """Fail-closed guard against a delayed cron recording a stale live quote."""

    CUTOFF = time(14, 0)

    def test_passes_before_cutoff(self):
        _assert_before_cutoff("atc", self.CUTOFF, datetime(2026, 6, 14, 13, 59, tzinfo=UTC))

    def test_raises_at_boundary(self):
        with pytest.raises(RuntimeError, match="atc capture attempted"):
            _assert_before_cutoff("atc", self.CUTOFF, datetime(2026, 6, 14, 14, 0, tzinfo=UTC))

    def test_raises_after_cutoff(self):
        with pytest.raises(RuntimeError, match="atc capture attempted"):
            _assert_before_cutoff("atc", self.CUTOFF, datetime(2026, 6, 14, 20, 36, tzinfo=UTC))


class TestAlreadyCaptured:
    """Idempotency: evening retries must skip once a complete ATC record exists."""

    def test_false_without_market_data(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert _already_captured("2026-06-14", "atc") is False

    def test_ignores_partial_and_other_dates(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        (mdir / "2026-06-14-163000-atc.json").write_text(json.dumps({"status": "partial"}))
        (mdir / "2026-06-13-163000-atc.json").write_text(json.dumps({"status": "complete"}))
        assert _already_captured("2026-06-14", "atc") is False

    def test_true_when_complete(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mdir = tmp_path / "market-data"
        mdir.mkdir()
        (mdir / "2026-06-14-170000-atc.json").write_text(json.dumps({"status": "complete"}))
        assert _already_captured("2026-06-14", "atc") is True


class TestSaveMarketDataAtomic:
    def test_writes_correct_content(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        record = {"date": "2026-06-14", "status": "complete"}
        filepath = save_market_data(record, "2026-06-14", "atc")
        assert json.loads(pathlib.Path(filepath).read_text()) == record
        # No leftover temp file.
        assert not list((tmp_path / "market-data").glob("*.tmp"))


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
