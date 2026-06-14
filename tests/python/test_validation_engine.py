"""Tests for validation_engine.py — regime derivation and comparison logic."""

import sys
import pathlib

# Ensure scripts/python is importable
sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from validation_engine import derive_actual_regime, compare_regimes

# --- derive_actual_regime ---


class TestDeriveActualRegime:
    """Cover all 6 regime outcomes + edge cases."""

    THRESHOLD = 0.02  # threshold_mean

    def test_bullish(self):
        assert derive_actual_regime(100.0, 101.0, 0.01, self.THRESHOLD) == "Bullish"

    def test_bearish(self):
        assert derive_actual_regime(100.0, 99.0, 0.01, self.THRESHOLD) == "Bearish"

    def test_sideways_positive(self):
        assert derive_actual_regime(100.0, 100.3, 0.01, self.THRESHOLD) == "Sideways"

    def test_sideways_negative(self):
        assert derive_actual_regime(100.0, 99.8, 0.01, self.THRESHOLD) == "Sideways"

    def test_sideways_zero(self):
        assert derive_actual_regime(100.0, 100.0, 0.01, self.THRESHOLD) == "Sideways"

    def test_risk_off(self):
        assert derive_actual_regime(100.0, 99.0, 0.03, self.THRESHOLD) == "Risk-Off"

    def test_crisis(self):
        assert derive_actual_regime(100.0, 97.5, 0.05, self.THRESHOLD) == "Crisis"

    def test_unclassified_positive_high_vol(self):
        """Positive return with high volatility doesn't match any regime."""
        result = derive_actual_regime(100.0, 101.0, 0.03, self.THRESHOLD)
        assert result == "Unclassified"

    def test_unclassified_small_negative_high_vol(self):
        """Small negative return with high volatility."""
        result = derive_actual_regime(100.0, 99.9, 0.03, self.THRESHOLD)
        assert result == "Unclassified"

    def test_crisis_boundary(self):
        """Crisis requires return < -2% AND volatility > 2x threshold."""
        assert derive_actual_regime(100.0, 97.9, 0.041, self.THRESHOLD) == "Crisis"

    def test_bullish_boundary(self):
        """Exactly 0.5% return is Sideways, not Bullish."""
        result = derive_actual_regime(100.0, 100.5, 0.01, self.THRESHOLD)
        assert result == "Sideways"

    def test_bearish_boundary(self):
        """Exactly -0.5% return is Sideways, not Bearish."""
        result = derive_actual_regime(100.0, 99.5, 0.01, self.THRESHOLD)
        assert result == "Sideways"


# --- compare_regimes ---


class TestCompareRegimes:
    def test_match(self):
        assert compare_regimes("Bullish", "Bullish") == "Match"

    def test_mismatch(self):
        assert compare_regimes("Bullish", "Bearish") == "Mismatch"

    def test_match_risk_off(self):
        assert compare_regimes("Risk-Off", "Risk-Off") == "Match"

    def test_mismatch_crisis_bullish(self):
        """Critical failure: Crisis predicted as Bullish."""
        assert compare_regimes("Bullish", "Crisis") == "Mismatch"

    def test_match_unclassified(self):
        assert compare_regimes("Unclassified", "Unclassified") == "Match"
