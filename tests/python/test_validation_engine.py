"""Tests for validation_engine.py — regime derivation and comparison logic."""

import json
import sys
from pathlib import Path

import pytest

# Ensure scripts/python is importable
sys.path.insert(0, str(Path(__file__).parents[2] / "scripts" / "python"))

from regime_rules import compare_regimes, derive_actual_regime
from validation_engine import (
    find_latest_market_file,
    find_latest_prediction_file,
    prune_orphan_validations,
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
    def setup_dirs(self, monkeypatch, tmp_path):
        # Create temp dirs for testing to avoid polluting workspace
        self.pred_dir = tmp_path / "predictions"
        self.market_dir = tmp_path / "market-data"
        self.val_dir = tmp_path / "validation"
        self.rep_dir = tmp_path / "reports"

        for d in (self.pred_dir, self.market_dir, self.val_dir, self.rep_dir):
            d.mkdir()

        # Monkeypatch constants in validation_engine
        monkeypatch.setattr("validation_engine.PREDICTIONS_DIR", str(self.pred_dir))
        monkeypatch.setattr("validation_engine.MARKET_DATA_DIR", str(self.market_dir))
        monkeypatch.setattr("validation_engine.VALIDATION_DIR", str(self.val_dir))
        monkeypatch.setattr("validation_engine.REPORTS_DIR", str(self.rep_dir))

    def test_find_latest_prediction_file(self):
        # 1. Write prediction file with am session suffix
        pred_am_path = self.pred_dir / "2026-06-16-090000-am.json"
        pred_am_path.write_text(json.dumps({"session": "am", "predictedRegime": "Bullish"}))

        found = find_latest_prediction_file(str(self.pred_dir), "2026-06-16", "am")
        assert found is not None
        assert Path(found).name == "2026-06-16-090000-am.json"

        # 2. Write prediction file with general naming but session in JSON
        pred_pm_path = self.pred_dir / "2026-06-16-140000.json"
        pred_pm_path.write_text(json.dumps({"session": "pm", "predictedRegime": "Sideways"}))

        found_pm = find_latest_prediction_file(str(self.pred_dir), "2026-06-16", "pm")
        assert found_pm is not None
        assert Path(found_pm).name == "2026-06-16-140000.json"

    def test_run_daily_validation_3_windows(self):
        # Write market data
        market_path = self.market_dir / "2026-06-16-163000.json"
        market_path.write_text(
            json.dumps({"actualRegime": "Bullish", "atoPrice": 100.0, "atcPrice": 101.0}),
        )

        # Write predictions for am, pm, and full_day
        (self.pred_dir / "2026-06-16-090000-am.json").write_text(
            json.dumps({"session": "am", "predictedRegime": "Bullish"}),
        )
        (self.pred_dir / "2026-06-16-140000-pm.json").write_text(
            json.dumps({"session": "pm", "predictedRegime": "Bearish"}),
        )
        (self.pred_dir / "2026-06-16-090000-full_day.json").write_text(
            json.dumps({"session": "full_day", "predictedRegime": "Bullish"}),
        )

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
        val_am = self.val_dir / "2026-06-16-am.json"
        val_am.write_text(
            json.dumps(
                {
                    "date": "2026-06-16",
                    "session": "am",
                    "predictedRegime": "Bullish",
                    "actualRegime": "Bullish",
                    "isCorrect": True,
                },
            ),
        )

        val_pm = self.val_dir / "2026-06-16-pm.json"
        val_pm.write_text(
            json.dumps(
                {
                    "date": "2026-06-16",
                    "session": "pm",
                    "predictedRegime": "Bearish",
                    "actualRegime": "Bullish",
                    "isCorrect": False,
                },
            ),
        )

        update_aggregate_metrics()

        metrics_file = self.rep_dir / "metrics.json"
        assert metrics_file.exists()

        metrics_data = json.loads(metrics_file.read_text())

        assert "by_window" in metrics_data["metrics"]
        by_window = metrics_data["metrics"]["by_window"]

        assert by_window["am"]["overall_accuracy"] == 1.0
        assert by_window["am"]["total_count"] == 1
        assert by_window["pm"]["overall_accuracy"] == 0.0
        assert by_window["pm"]["total_count"] == 1
        assert by_window["full_day"]["total_count"] == 0

    def test_update_aggregate_metrics_rolling_and_hit_rates(self):
        # Create 10 days of data to test rolling 7D
        for i in range(1, 11):
            date_str = f"2026-06-{i:02d}"
            val_file = self.val_dir / f"{date_str}-full_day.json"
            # First 5 correct, next 5 incorrect
            is_correct = i <= 5
            val_file.write_text(
                json.dumps(
                    {
                        "date": date_str,
                        "session": "full_day",
                        "predictedRegime": "Bullish",
                        "actualRegime": "Bullish" if is_correct else "Bearish",
                        "isCorrect": is_correct,
                    },
                ),
            )

        update_aggregate_metrics()

        metrics_file = self.rep_dir / "metrics.json"
        data = json.loads(metrics_file.read_text())

        metrics = data["metrics"]
        assert metrics["total_count"] == 10
        assert metrics["overall_accuracy"] == 0.5
        # Rolling 7D at day 10: days 4,5 (correct) and 6,7,8,9,10 (incorrect) -> 2/7 approx 0.2857
        assert round(metrics["rolling_7d"], 4) == round(2 / 7, 4)

        # Hit rates
        assert (
            metrics["hit_rates"]["Bullish"] == 1.0
        )  # All predicted bullish when actual was bullish were correct
        assert metrics["hit_rates"]["Bearish"] == 0.0  # All actual bearish were predicted bullish

    def test_empty_validation_dir(self):
        """Should handle empty directory gracefully."""
        # Setup already creates empty dirs
        update_aggregate_metrics()
        # Should not crash, maybe print a warning (captured in logs)
        assert not (self.rep_dir / "metrics.json").exists()

    def test_unclassified_regime(self):
        """Ensure Unclassified regime is handled in metrics."""
        val_file = self.val_dir / "2026-06-16-full_day.json"
        val_file.write_text(
            json.dumps(
                {
                    "date": "2026-06-16",
                    "session": "full_day",
                    "predictedRegime": "Unclassified",
                    "actualRegime": "Sideways",
                    "isCorrect": False,
                },
            ),
        )

        update_aggregate_metrics()
        metrics_file = self.rep_dir / "metrics.json"
        data = json.loads(metrics_file.read_text())

        # Unclassified is not in VALID_REGIMES so it won't be in hit_rates or confusion_matrix rows
        # but it will be in the actuals if it was an actual regime.
        # Here it was predicted.
        assert data["metrics"]["total_count"] == 1

    def test_find_latest_market_file_prefers_atc(self):
        """Ensure find_latest_market_file prefers *-atc.json over *-ato.json."""
        # 'ato' is alphabetically after 'atc'
        (self.market_dir / "2026-06-16-100000-ato.json").write_text(
            json.dumps({"status": "partial", "atoPrice": 100.0}),
        )
        atc_data = {
            "status": "complete",
            "actualRegime": "Bearish",
            "atoPrice": 100.0,
            "atcPrice": 98.0,
        }
        (self.market_dir / "2026-06-16-163000-atc.json").write_text(json.dumps(atc_data))

        found = find_latest_market_file(str(self.market_dir), "2026-06-16")
        assert found is not None
        assert Path(found).name == "2026-06-16-163000-atc.json"

    def test_prune_orphan_validations(self):
        """Ensure orphan validation files referencing missing predictions are removed."""
        # Valid validation record with existing prediction
        (self.pred_dir / "2026-06-16-090000-am.json").write_text(
            json.dumps({"session": "am", "predictedRegime": "Bullish"}),
        )
        (self.val_dir / "2026-06-16-090000-am.json").write_text(
            json.dumps(
                {
                    "file_id": "2026-06-16-090000-am",
                    "observationAbout": [{"@id": "predictions/2026-06-16-090000-am.json"}],
                },
            ),
        )

        # Orphan validation record whose prediction does NOT exist
        orphan_file = self.val_dir / "2026-06-16-999999-orphan.json"
        orphan_file.write_text(
            json.dumps(
                {
                    "file_id": "2026-06-16-999999-orphan",
                    "observationAbout": [{"@id": "predictions/2026-06-16-999999-orphan.json"}],
                },
            ),
        )

        pruned_count = prune_orphan_validations()
        assert pruned_count == 1
        assert not orphan_file.exists()
        assert (self.val_dir / "2026-06-16-090000-am.json").exists()

    def test_run_daily_validation_with_ato_and_atc_files(self):
        """End-to-end: with both ATO and ATC files present, evaluate against ATC outcome."""
        (self.market_dir / "2026-06-16-100000-ato.json").write_text(
            json.dumps({"status": "partial", "atoPrice": 100.0}),
        )
        atc_data = {
            "status": "complete",
            "actualRegime": "Bearish",
            "atoPrice": 100.0,
            "atcPrice": 98.0,
        }
        (self.market_dir / "2026-06-16-163000-atc.json").write_text(json.dumps(atc_data))
        (self.pred_dir / "2026-06-16-140000-pm.json").write_text(
            json.dumps({"session": "pm", "predictedRegime": "Sideways"}),
        )

        records = run_daily_validation("2026-06-16")
        assert len(records) == 1
        assert records[0]["session"] == "pm"
        assert records[0]["predictedRegime"] == "Sideways"
        assert records[0]["actualRegime"] == "Bearish"
        assert records[0]["isCorrect"] is False
        assert records[0]["deviationScore"] == 1.0
