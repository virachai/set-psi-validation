"""Tests for validation_engine.py — regime derivation and comparison logic."""

import sys
import pathlib
import os
import json
import shutil
import tempfile
import pytest

# Ensure scripts/python is importable
sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from validation_engine import (
    derive_actual_regime,
    compare_regimes,
    find_latest_prediction_file,
    run_daily_validation,
    update_aggregate_metrics,
)

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
        assert compare_regimes("Bullish", "Bullish") is True

    def test_mismatch(self):
        assert compare_regimes("Bullish", "Bearish") is False

    def test_match_risk_off(self):
        assert compare_regimes("Risk-Off", "Risk-Off") is True

    def test_mismatch_crisis_bullish(self):
        """Critical failure: Crisis predicted as Bullish."""
        assert compare_regimes("Bullish", "Crisis") is False

    def test_match_unclassified(self):
        assert compare_regimes("Unclassified", "Unclassified") is True


# --- Three-Window Validation and Metrics ---


class TestThreeWindowValidation:
    @pytest.fixture(autouse=True)
    def setup_dirs(self, monkeypatch):
        # Create temp dirs for testing to avoid polluting workspace
        self.temp_dir = tempfile.mkdtemp()
        self.pred_dir = os.path.join(self.temp_dir, "predictions")
        self.market_dir = os.path.join(self.temp_dir, "market-data")
        self.val_dir = os.path.join(self.temp_dir, "validation")
        self.rep_dir = os.path.join(self.temp_dir, "reports")

        os.makedirs(self.pred_dir)
        os.makedirs(self.market_dir)
        os.makedirs(self.val_dir)
        os.makedirs(self.rep_dir)

        # Monkeypatch constants in validation_engine
        monkeypatch.setattr("validation_engine.PREDICTIONS_DIR", self.pred_dir)
        monkeypatch.setattr("validation_engine.MARKET_DATA_DIR", self.market_dir)
        monkeypatch.setattr("validation_engine.VALIDATION_DIR", self.val_dir)
        monkeypatch.setattr("validation_engine.REPORTS_DIR", self.rep_dir)

        yield
        shutil.rmtree(self.temp_dir)

    def test_find_latest_prediction_file(self):
        # 1. Write prediction file with am session suffix
        pred_am_path = os.path.join(self.pred_dir, "2026-06-16-090000-am.json")
        with open(pred_am_path, "w") as f:
            json.dump({"session": "am", "predictedRegime": "Bullish"}, f)

        found = find_latest_prediction_file(self.pred_dir, "2026-06-16", "am")
        assert found is not None
        assert os.path.basename(found) == "2026-06-16-090000-am.json"

        # 2. Write prediction file with general naming but session in JSON
        pred_pm_path = os.path.join(self.pred_dir, "2026-06-16-140000.json")
        with open(pred_pm_path, "w") as f:
            json.dump({"session": "pm", "predictedRegime": "Sideways"}, f)

        found_pm = find_latest_prediction_file(self.pred_dir, "2026-06-16", "pm")
        assert found_pm is not None
        assert os.path.basename(found_pm) == "2026-06-16-140000.json"

    def test_run_daily_validation_3_windows(self):
        # Write market data
        market_path = os.path.join(self.market_dir, "2026-06-16-163000.json")
        with open(market_path, "w") as f:
            json.dump({"actualRegime": "Bullish", "atoPrice": 100.0, "atcPrice": 101.0}, f)

        # Write predictions for am, pm, and full_day
        with open(os.path.join(self.pred_dir, "2026-06-16-090000-am.json"), "w") as f:
            json.dump({"session": "am", "predictedRegime": "Bullish"}, f)
        with open(os.path.join(self.pred_dir, "2026-06-16-140000-pm.json"), "w") as f:
            json.dump({"session": "pm", "predictedRegime": "Bearish"}, f)
        with open(os.path.join(self.pred_dir, "2026-06-16-090000-full_day.json"), "w") as f:
            json.dump({"session": "full_day", "predictedRegime": "Bullish"}, f)

        records = run_daily_validation("2026-06-16")
        assert len(records) == 3

        sessions = [r["session"] for r in records]
        assert "am" in sessions
        assert "pm" in sessions
        assert "full_day" in sessions

        # Validate correctness values
        for r in records:
            if r["session"] == "am":
                assert r["isCorrect"] is True
            elif r["session"] == "pm":
                assert r["isCorrect"] is False
            elif r["session"] == "full_day":
                assert r["isCorrect"] is True

    def test_update_aggregate_metrics_by_window(self):
        # Create validation files manually
        val_am = os.path.join(self.val_dir, "2026-06-16-am.json")
        with open(val_am, "w") as f:
            json.dump(
                {
                    "date": "2026-06-16",
                    "session": "am",
                    "predictedRegime": "Bullish",
                    "actualRegime": "Bullish",
                    "isCorrect": True,
                },
                f,
            )

        val_pm = os.path.join(self.val_dir, "2026-06-16-pm.json")
        with open(val_pm, "w") as f:
            json.dump(
                {
                    "date": "2026-06-16",
                    "session": "pm",
                    "predictedRegime": "Bearish",
                    "actualRegime": "Bullish",
                    "isCorrect": False,
                },
                f,
            )

        update_aggregate_metrics()

        metrics_file = os.path.join(self.rep_dir, "metrics.json")
        assert os.path.exists(metrics_file)

        with open(metrics_file, "r") as f:
            metrics_data = json.load(f)

        assert "by_window" in metrics_data["metrics"]
        by_window = metrics_data["metrics"]["by_window"]

    def test_update_aggregate_metrics_rolling_and_hit_rates(self):
        # Create 10 days of data to test rolling 7D
        for i in range(1, 11):
            date_str = f"2026-06-{i:02d}"
            val_file = os.path.join(self.val_dir, f"{date_str}-full_day.json")
            # First 5 correct, next 5 incorrect
            is_correct = i <= 5
            with open(val_file, "w") as f:
                json.dump(
                    {
                        "date": date_str,
                        "session": "full_day",
                        "predictedRegime": "Bullish",
                        "actualRegime": "Bullish" if is_correct else "Bearish",
                        "isCorrect": is_correct,
                    },
                    f,
                )

        update_aggregate_metrics()

        metrics_file = os.path.join(self.rep_dir, "metrics.json")
        with open(metrics_file, "r") as f:
            data = json.load(f)

        metrics = data["metrics"]
        assert metrics["total_count"] == 10
        assert metrics["overall_accuracy"] == 0.5
        # Rolling 7D at day 10: days 4,5 (correct) and 6,7,8,9,10 (incorrect) -> 2/7 approx 0.2857
        assert round(metrics["rolling_7d"], 4) == round(2 / 7, 4)
        
        # Hit rates
        assert metrics["hit_rates"]["Bullish"] == 1.0 # All predicted bullish when actual was bullish were correct
        assert metrics["hit_rates"]["Bearish"] == 0.0 # All actual bearish were predicted bullish

    def test_empty_validation_dir(self):
        """Should handle empty directory gracefully."""
        # Setup already creates empty dirs
        update_aggregate_metrics()
        # Should not crash, maybe print a warning (captured in logs)
        assert not os.path.exists(os.path.join(self.rep_dir, "metrics.json"))

    def test_unclassified_regime(self):
        """Ensure Unclassified regime is handled in metrics."""
        val_file = os.path.join(self.val_dir, "2026-06-16-full_day.json")
        with open(val_file, "w") as f:
            json.dump(
                {
                    "date": "2026-06-16",
                    "session": "full_day",
                    "predictedRegime": "Unclassified",
                    "actualRegime": "Sideways",
                    "isCorrect": False,
                },
                f,
            )
        
        update_aggregate_metrics()
        metrics_file = os.path.join(self.rep_dir, "metrics.json")
        with open(metrics_file, "r") as f:
            data = json.load(f)
        
        # Unclassified is not in VALID_REGIMES so it won't be in hit_rates or confusion_matrix rows
        # but it will be in the actuals if it was an actual regime.
        # Here it was predicted.
        assert data["metrics"]["total_count"] == 1
