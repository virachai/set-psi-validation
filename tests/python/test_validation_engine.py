"""Tests for validation_engine.py — regime derivation and comparison logic."""

import json
import sys
from datetime import time
from pathlib import Path

import pytest

# Ensure scripts/python is importable
sys.path.insert(0, str(Path(__file__).parents[2] / "scripts" / "python"))

import audit_truth_layer
from audit_truth_layer import run_deep_audit
from capture_market import save_market_data
from predictions_loader import build_snapshot, save_snapshot
from regime_rules import compare_regimes, derive_actual_regime
from validation_engine import (
    _resolve_market_outcome,
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

    def test_unclassified_never_counts_as_match(self):
        """Unclassified means a real classification failed on one or both sides —
        it must never be scored as a correct prediction, even against itself."""
        assert compare_regimes("Unclassified", "Unclassified") is False


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

        # 2. Write prediction file with explicit session suffix
        pred_pm_path = self.pred_dir / "2026-06-16-140000-pm.json"
        pred_pm_path.write_text(json.dumps({"session": "pm", "predictedRegime": "Sideways"}))

        found_pm = find_latest_prediction_file(str(self.pred_dir), "2026-06-16", "pm")
        assert found_pm is not None
        assert Path(found_pm).name == "2026-06-16-140000-pm.json"

    def test_run_daily_validation_full_day_only(self):
        """Single cycle: only the full_day prediction is scored; legacy am/pm are ignored."""
        (self.market_dir / "2026-06-16-163000-atc.json").write_text(
            json.dumps({"actualRegime": "Bullish"}),
        )
        (self.pred_dir / "2026-06-16-090000-am.json").write_text(
            json.dumps({"session": "am", "predictedRegime": "Bearish"}),
        )
        (self.pred_dir / "2026-06-16-090000-full_day.json").write_text(
            json.dumps({"session": "full_day", "predictedRegime": "Bullish"}),
        )

        records = run_daily_validation("2026-06-16")
        assert len(records) == 1
        assert records[0]["session"] == "full_day"
        assert records[0]["isCorrect"] is True

    def test_artifact_chain_prediction_market_validation_metrics(self, monkeypatch):
        monkeypatch.setattr("predictions_loader.PREDICTIONS_DIR", str(self.pred_dir))
        monkeypatch.setattr("capture_market.MARKET_DATA_DIR", str(self.market_dir))

        prediction = build_snapshot(
            {"data": {"regime": "SIDEWAYS", "psi": 0.8}},
            session="full_day",
        )
        prediction.update(
            {
                "observationDate": "2026-06-16T09:30:00+07:00",
                "timestamp": "2026-06-16T09:30:00+07:00",
                "date": "2026-06-16",
            },
        )
        prediction_path = save_snapshot(prediction)
        assert Path(prediction_path).exists()

        market_path = save_market_data(
            {
                "actualRegime": "Sideways",
                "status": "ok",
                "observationPeriod": "2026-06-16T10:00:00+07:00/2026-06-16T16:30:00+07:00",
            },
            "2026-06-16",
            "atc",
            captured_at=time(16, 30),
        )
        assert Path(market_path).exists()

        records = run_daily_validation("2026-06-16")
        assert len(records) == 1
        assert records[0]["session"] == "full_day"
        assert records[0]["predictedRegime"] == "Sideways"
        assert records[0]["actualRegime"] == "Sideways"
        assert records[0]["isCorrect"] is True
        assert records[0]["status"] == "complete"
        assert list(self.val_dir.glob("*.json"))

        update_aggregate_metrics()
        metrics = json.loads((self.rep_dir / "metrics.json").read_text())
        assert metrics["metrics"]["overall_accuracy"] == 1.0
        assert metrics["metrics"]["by_window"]["full_day"]["total_count"] == 1
        assert metrics["metrics"]["by_window"]["full_day"]["overall_accuracy"] == 1.0

    def test_truth_audit_classifies_historical_missing_prediction(self):
        audit_truth_layer.PREDICTIONS_DIR = self.pred_dir
        audit_truth_layer.MARKET_DATA_DIR = self.market_dir
        audit_truth_layer.REPORTS_DIR = self.rep_dir

        (self.market_dir / "2026-09-08-164500-atc.json").write_text(
            '{"actualRegime": "Sideways"}',
            encoding="utf-8",
        )
        (self.market_dir / "2026-09-09-164500-atc.json").write_text(
            '{"actualRegime": "Sideways"}',
            encoding="utf-8",
        )
        (self.pred_dir / "2026-09-09-093000-full_day.json").write_text(
            '{"predictedRegime": "Sideways"}',
            encoding="utf-8",
        )

        report = run_deep_audit()

        assert report["missingMatches"] == []
        assert report["expectedMissingMatches"] == [
            {
                "date": "2026-09-08",
                "session": "full_day",
                "file": str(self.market_dir / "2026-09-08-164500-atc.json"),
                "classification": "expected_missing",
            },
        ]

    def test_truth_audit_flags_missing_prediction_after_retained_start(self):
        audit_truth_layer.PREDICTIONS_DIR = self.pred_dir
        audit_truth_layer.MARKET_DATA_DIR = self.market_dir
        audit_truth_layer.REPORTS_DIR = self.rep_dir

        (self.pred_dir / "2026-09-09-093000-full_day.json").write_text(
            '{"predictedRegime": "Sideways"}',
            encoding="utf-8",
        )
        (self.market_dir / "2026-09-10-164500-atc.json").write_text(
            '{"actualRegime": "Sideways"}',
            encoding="utf-8",
        )

        report = run_deep_audit()

        assert report["missingMatches"] == [
            {
                "date": "2026-09-10",
                "session": "full_day",
                "file": str(self.market_dir / "2026-09-10-164500-atc.json"),
                "classification": "unexpected_missing",
            },
        ]
        assert report["expectedMissingMatches"] == []

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

        # Single cycle: only full_day is broken out; legacy am/pm still count overall.
        assert set(by_window) == {"full_day"}
        assert by_window["full_day"]["total_count"] == 0
        assert metrics_data["metrics"]["total_count"] == 2

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

    def test_run_daily_validation_with_legacy_ato_and_atc_files(self):
        """A legacy ATO file alongside the ATC file must not shadow the ATC outcome."""
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
        (self.pred_dir / "2026-06-16-090000-full_day.json").write_text(
            json.dumps({"session": "full_day", "predictedRegime": "Sideways"}),
        )

        records = run_daily_validation("2026-06-16")
        assert len(records) == 1
        assert records[0]["actualRegime"] == "Bearish"
        assert records[0]["isCorrect"] is False

    def test_run_daily_validation_skips_when_no_market_file(self):
        """No market capture yet for this date: write no validation file at all."""
        (self.pred_dir / "2026-06-16-090000-full_day.json").write_text(
            json.dumps({"session": "full_day", "predictedRegime": "Bullish"}),
        )

        records = run_daily_validation("2026-06-16")
        assert records == []
        assert not list(self.val_dir.glob("*.json"))

    def test_full_day_ignores_legacy_noon_file_before_atc(self):
        """A legacy noon capture carries a morning-window actualRegime — it must not
        complete full_day before the ATC capture exists."""
        (self.market_dir / "2026-06-16-123000-noon.json").write_text(
            json.dumps({"status": "complete", "actualRegime": "Bullish"}),
        )
        (self.pred_dir / "2026-06-16-090000-full_day.json").write_text(
            json.dumps({"session": "full_day", "predictedRegime": "Bullish"}),
        )

        assert _resolve_market_outcome("2026-06-16") is None
        records = run_daily_validation("2026-06-16")
        assert [r for r in records if r["session"] == "full_day"] == []
        assert not (self.val_dir / "2026-06-16-090000-full_day.json").exists()

    def test_update_aggregate_metrics_excludes_pending_records(self):
        """Pending records (no actualRegime resolved) must not pollute accuracy/rolling metrics."""
        (self.val_dir / "2026-06-16-full_day.json").write_text(
            json.dumps(
                {
                    "date": "2026-06-16",
                    "session": "full_day",
                    "status": "complete",
                    "predictedRegime": "Bullish",
                    "actualRegime": "Bullish",
                    "isCorrect": True,
                },
            ),
        )
        (self.val_dir / "2026-06-17-full_day.json").write_text(
            json.dumps(
                {
                    "date": "2026-06-17",
                    "session": "full_day",
                    "status": "pending",
                    "predictedRegime": "Bearish",
                    "actualRegime": None,
                    "isCorrect": None,
                },
            ),
        )

        update_aggregate_metrics()
        data = json.loads((self.rep_dir / "metrics.json").read_text())

        assert data["metrics"]["total_count"] == 1
        assert data["metrics"]["overall_accuracy"] == 1.0

    def test_rolling_window_dedupes_multi_session_same_date(self):
        """A date with am+pm+full_day sessions must contribute one row to the
        rolling window, not three — otherwise a nominal 7-day window spans
        fewer than 7 actual trading days."""
        dates = [f"2026-06-{i:02d}" for i in range(1, 8)]
        for i, date_str in enumerate(dates):
            # Every date's 3 sessions agree: correct on the last date only.
            is_correct = i == len(dates) - 1
            for session in ("am", "pm", "full_day"):
                val_file = self.val_dir / f"{date_str}-{session}.json"
                val_file.write_text(
                    json.dumps(
                        {
                            "date": date_str,
                            "session": session,
                            "predictedRegime": "Bullish",
                            "actualRegime": "Bullish" if is_correct else "Bearish",
                            "isCorrect": is_correct,
                        },
                    ),
                )

        update_aggregate_metrics()
        data = json.loads((self.rep_dir / "metrics.json").read_text())

        # 7 distinct trading dates, only the last is fully correct -> 1/7,
        # not 1/21 (which row-counting would have produced) or diluted by
        # same-day duplicates.
        assert round(data["metrics"]["rolling_7d"], 4) == round(1 / 7, 4)

    def test_update_aggregate_metrics_computes_precision_and_f1(self):
        """Precision/F1 per regime, derived from the same confusion matrix as hit_rates."""
        # 2 correct Bullish predictions, 1 Bullish prediction that was actually Bearish.
        records = [
            {"predictedRegime": "Bullish", "actualRegime": "Bullish", "isCorrect": True},
            {"predictedRegime": "Bullish", "actualRegime": "Bullish", "isCorrect": True},
            {"predictedRegime": "Bullish", "actualRegime": "Bearish", "isCorrect": False},
        ]
        for i, rec in enumerate(records):
            date_str = f"2026-06-{i + 1:02d}"
            (self.val_dir / f"{date_str}-full_day.json").write_text(
                json.dumps({"date": date_str, "session": "full_day", **rec}),
            )

        update_aggregate_metrics()
        data = json.loads((self.rep_dir / "metrics.json").read_text())
        metrics = data["metrics"]

        # Precision(Bullish) = correct Bullish predictions / all Bullish predictions = 2/3
        assert round(metrics["precision"]["Bullish"], 4) == round(2 / 3, 4)
        # Recall(Bullish) = correct Bullish predictions / all actual Bullish = 2/2 = 1.0
        assert metrics["hit_rates"]["Bullish"] == 1.0
        # F1 is the harmonic mean of precision and recall.
        expected_f1 = 2 * (2 / 3) * 1.0 / ((2 / 3) + 1.0)
        assert round(metrics["f1"]["Bullish"], 4) == round(expected_f1, 4)

    def test_update_aggregate_metrics_f1_is_zero_not_none_when_all_wrong(self):
        """Defined precision/recall of 0.0 must yield F1 0.0; None is reserved for no data."""
        # Bullish and Bearish each predicted and each occurred, but never matched.
        records = [
            {"predictedRegime": "Bullish", "actualRegime": "Bearish", "isCorrect": False},
            {"predictedRegime": "Bearish", "actualRegime": "Bullish", "isCorrect": False},
        ]
        for i, rec in enumerate(records):
            date_str = f"2026-06-{i + 1:02d}"
            (self.val_dir / f"{date_str}-full_day.json").write_text(
                json.dumps({"date": date_str, "session": "full_day", **rec}),
            )

        update_aggregate_metrics()
        metrics = json.loads((self.rep_dir / "metrics.json").read_text())["metrics"]

        assert metrics["precision"]["Bullish"] == 0.0
        assert metrics["hit_rates"]["Bullish"] == 0.0
        assert metrics["f1"]["Bullish"] == 0.0
        assert metrics["f1"]["Bearish"] == 0.0
        # Never predicted and never occurred -> undefined, not zero.
        assert metrics["f1"]["Sideways"] is None


class TestResolveMarketOutcome:
    """Single cycle: the outcome is always the ATC file's full-day actualRegime (RFC 020)."""

    @pytest.fixture(autouse=True)
    def setup_dirs(self, monkeypatch, tmp_path):
        self.market_dir = tmp_path / "market-data"
        self.market_dir.mkdir()
        monkeypatch.setattr("validation_engine.MARKET_DATA_DIR", str(self.market_dir))

    def _write(self, name: str, data: dict) -> None:
        (self.market_dir / name).write_text(json.dumps(data))

    def test_uses_atc_actual_regime(self):
        self._write(
            "2026-06-16-123000-noon.json",
            {"status": "complete", "actualRegime": "Sideways"},
        )
        self._write(
            "2026-06-16-163000-atc.json",
            {
                "status": "complete",
                "actualRegime": "Bearish",
                "afternoonRegime": "Bullish",
            },
        )

        market_path, regime, fallback_used = _resolve_market_outcome("2026-06-16")
        assert regime == "Bearish"
        assert market_path.endswith("-atc.json")
        assert fallback_used is False

    def test_no_market_data_returns_none(self):
        assert _resolve_market_outcome("2026-06-16") is None
