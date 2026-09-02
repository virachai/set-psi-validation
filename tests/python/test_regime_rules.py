"""Tests for regime_rules.py — canonical market regime derivation logic."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from regime_rules import (
    VALID_REGIMES,
    compare_regimes,
    compute_deviation_score,
    derive_actual_regime,
)


class TestCanonicalRegimeRules:
    """Cover all regime derivation cases and edge boundaries."""

    THRESHOLD = 0.02

    def test_valid_regimes_content(self):
        assert "Bullish" in VALID_REGIMES
        assert "Bearish" in VALID_REGIMES
        assert "Sideways" in VALID_REGIMES
        assert "Risk-Off" in VALID_REGIMES
        assert "Crisis" in VALID_REGIMES
        assert "Unclassified" in VALID_REGIMES

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

    def test_zero_or_negative_ato(self):
        """Zero or negative open price must return Unclassified, not raise ZeroDivisionError."""
        assert derive_actual_regime(0.0, 100.0, 0.01, self.THRESHOLD) == "Unclassified"
        assert derive_actual_regime(-100.0, 100.0, 0.01, self.THRESHOLD) == "Unclassified"

    def test_unclassified_high_vol_positive_return(self):
        assert derive_actual_regime(100.0, 101.0, 0.03, self.THRESHOLD) == "Unclassified"

    def test_compare_regimes(self):
        assert compare_regimes("Bullish", "Bullish") is True
        assert compare_regimes("Bullish", "Bearish") is False
        assert compare_regimes("Unclassified", "Unclassified") is True

    def test_compute_deviation_score(self):
        assert compute_deviation_score("Bullish", "Bullish") == 0.0
        assert compute_deviation_score("Bullish", "Bearish") == 1.0
