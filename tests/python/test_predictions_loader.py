"""Tests for predictions_loader.py — API response parsing and snapshot building."""

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

SAMPLE_RAPIDAPI_RESPONSE = {
    "status": "success",
    "data": {
        "regime": "SIDEWAYS",
        "psi": 0.8,
        "vix_level": 20,
    },
}


class TestBuildSnapshot:
    def test_valid_regime_output(self):
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        assert snapshot["@context"] == "https://schema.org"
        assert snapshot["@type"] == "Observation"
        assert snapshot["measuredProperty"]["@type"] == "DefinedTerm"
        assert snapshot["measuredProperty"]["inDefinedTermSet"] == REGIME_TAXONOMY_URL
        assert snapshot["predictedRegime"] == "Risk-Off"  # normalised from RISK_OFF

    def test_psi_score_in_variable_measured(self):
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        measures = {m["name"]: m["value"] for m in snapshot["variableMeasured"]}
        assert measures["PSI Score"] == 0.41
        assert measures["Predicted Regime"] == "Risk-Off"

    def test_psi_score_bounds(self):
        """PSI Score should have explicit min/max."""
        snapshot = build_snapshot(SAMPLE_API_RESPONSE)
        psi_entry = next(
            m for m in snapshot["variableMeasured"] if m["name"] == "PSI Score"
        )
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
        assert snapshot["predictedRegime"] == "Risk-Off"  # normalised from RISK_OFF
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

    # --- RapidAPI format ---

    def test_rapidapi_wrapped_format(self):
        """RapidAPI returns {status, data: {regime, psi}} — must unwrap and normalise case."""
        snapshot = build_snapshot(SAMPLE_RAPIDAPI_RESPONSE)
        assert snapshot["predictedRegime"] == "Sideways"  # normalised from SIDEWAYS
        assert snapshot["psiScore"] == 0.8
        assert snapshot["modelId"] == "PSI Engine v1"

    def test_rapidapi_regime_in_valid_list(self):
        snapshot = build_snapshot(SAMPLE_RAPIDAPI_RESPONSE)
        assert snapshot["predictedRegime"] in VALID_REGIMES

    def test_rapidapi_schema_org_fields(self):
        snapshot = build_snapshot(SAMPLE_RAPIDAPI_RESPONSE)
        assert snapshot["@type"] == "Observation"
        assert snapshot["@context"] == "https://schema.org"

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("SIDEWAYS", "Sideways"),
            ("sideways", "Sideways"),
            ("BULLISH", "Bullish"),
            ("bearish", "Bearish"),
            ("RISK_OFF", "Risk-Off"),
            ("risk_off", "Risk-Off"),
            ("RISKOFF", "Risk-Off"),  # no separator
            ("CRISIS", "Crisis"),
        ],
    )
    def test_case_normalisation(self, raw, expected):
        snapshot = build_snapshot({"regime": raw, "psi": 0.5})
        assert snapshot["predictedRegime"] == expected

    # --- Native schema.org (Lambda) format ---

    SAMPLE_LAMBDA_SCHEMA_ORG = {
        "@context": "https://schema.org",
        "@type": "Observation",
        "name": "PSI Prediction 2026-06-14",
        "observationDate": "2026-06-14T10:00:00.000Z",
        "measuredProperty": {
            "@type": "DefinedTerm",
            "name": "Predicted Regime",
            "inDefinedTermSet": REGIME_TAXONOMY_URL,
        },
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "name": "PSI Score",
                "value": 0.8,
                "minValue": 0,
                "maxValue": 1,
            },
            {"@type": "PropertyValue", "name": "Predicted Regime", "value": "SIDEWAYS"},
            {"@type": "PropertyValue", "name": "VIX Level", "value": 20},
        ],
    }

    def test_lambda_schema_org_passthrough(self):
        """Native schema.org from Lambda should pass through with backward-compat fields added."""
        snapshot = build_snapshot(self.SAMPLE_LAMBDA_SCHEMA_ORG)
        assert snapshot["@type"] == "Observation"
        assert snapshot["name"] == "PSI Prediction 2026-06-14"
        # Passthrough: @context, measuredProperty, variableMeasured preserved
        assert snapshot["@context"] == "https://schema.org"
        assert snapshot["measuredProperty"]["name"] == "Predicted Regime"
        # Backward-compat fields added
        assert snapshot["date"] is not None
        assert snapshot["timestamp"] is not None
        assert snapshot["predictedRegime"] == "Sideways"  # normalised from SIDEWAYS
        assert snapshot["psiScore"] == 0.8
        assert snapshot["modelId"] == "PSI Engine v1 (Lambda)"

    def test_lambda_schema_org_preserves_additional_property(self):
        """additionalProperty from Lambda must survive passthrough."""
        data = dict(self.SAMPLE_LAMBDA_SCHEMA_ORG)
        data["additionalProperty"] = [
            {"@type": "PropertyValue", "name": "Avg Equity Change", "value": 0.23},
        ]
        snapshot = build_snapshot(data)
        assert "additionalProperty" in snapshot
        assert snapshot["additionalProperty"][0]["name"] == "Avg Equity Change"

    def test_lambda_schema_org_regime_normalisation(self):
        """Case/separator normalisation must still apply on passthrough path."""
        data = dict(self.SAMPLE_LAMBDA_SCHEMA_ORG)
        data["variableMeasured"][1]["value"] = "RISKOFF"
        snapshot = build_snapshot(data)
        assert snapshot["predictedRegime"] == "Risk-Off"
