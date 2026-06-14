"""Tests for predictions_loader.py — API response parsing and snapshot building."""

import json
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "scripts" / "python"))

from predictions_loader import build_snapshot, VALID_REGIMES, REGIME_TAXONOMY_URL


SAMPLE_API_RESPONSE = {
    "predictedRegime": "RISK_OFF",
    "psiScore": 0.41,
    "modelId": "psi-engine-v1",
}


class TestBuildSnapshot:
    def test_valid_regime_output(self):
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        assert snapshot["@context"] == "https://schema.org"
        assert snapshot["@type"] == "Observation"
        assert snapshot["measuredProperty"]["@type"] == "DefinedTerm"
        assert snapshot["measuredProperty"]["inDefinedTermSet"] == REGIME_TAXONOMY_URL
        assert snapshot["predictedRegime"] == "RISK_OFF"

    def test_psi_score_in_variable_measured(self):
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        measures = {m["name"]: m["value"] for m in snapshot["variableMeasured"]}
        assert measures["PSI Score"] == 0.41
        assert measures["Predicted Regime"] == "RISK_OFF"

    def test_psi_score_bounds(self):
        """PSI Score should have explicit min/max."""
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        psi_entry = next(m for m in snapshot["variableMeasured"] if m["name"] == "PSI Score")
        assert psi_entry["minValue"] == 0
        assert psi_entry["maxValue"] == 1

    def test_measurement_method(self):
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        assert snapshot["measurementMethod"]["@type"] == "DefinedTerm"
        assert snapshot["measurementMethod"]["name"] == "psi-engine-v1"

    def test_backward_compat_fields(self):
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        assert snapshot["timestamp"] is not None
        assert snapshot["date"] is not None
        assert snapshot["predictedRegime"] == "RISK_OFF"
        assert snapshot["psiScore"] == 0.41
        assert snapshot["modelId"] == "psi-engine-v1"

    def test_unknown_regime_warns(self):
        """Unknown regime should still be passed through with a warning."""
        data = {**SAMPLE_API_RESPONSE, "predictedRegime": "UNKNOWN_REGIME"}
        snapshot = build_snapshot(data)
        assert snapshot["predictedRegime"] == "UNKNOWN_REGIME"

    def test_missing_psi_score_defaults(self):
        data = {"predictedRegime": "Bullish"}
        snapshot = build_snapshot(data)
        assert snapshot["psiScore"] == 0.0

    def test_missing_model_id_defaults(self):
        data = {"predictedRegime": "Bullish", "psiScore": 0.5}
        snapshot = build_snapshot(data)
        assert snapshot["modelId"] == "PSI Engine v1"

    @pytest.mark.parametrize("regime", VALID_REGIMES)
    def test_all_valid_regimes(self, regime):
        """All valid regimes should produce a correct snapshot."""
        data = {"predictedRegime": regime, "psiScore": 0.5, "modelId": "test"}
        snapshot = build_snapshot(data)
        assert snapshot["predictedRegime"] == regime
        measures = {m["name"]: m["value"] for m in snapshot["variableMeasured"]}
        assert measures["Predicted Regime"] == regime

    def test_schema_org_observation_contract(self):
        """Verify all required schema.org Observation fields."""
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        assert "@context" in snapshot
        assert "@type" in snapshot
        assert "name" in snapshot
        assert "observationDate" in snapshot
        assert "measuredProperty" in snapshot
        assert "variableMeasured" in snapshot
        assert "measurementMethod" in snapshot
