# /// script
# dependencies = ["httpx", "python-dotenv"]
# ///
"""
PSI Prediction Loader

Fetches the PSI regime prediction from the external PSI Engine API (Pre-ATO)
and saves it as a schema.org-compliant Observation JSON-LD file.

Output: predictions/YYYY-MM-DD.json

Governance: Compliant with "Lean PSI Validator" principles.
"""

import os
import json
import sys
from datetime import datetime, timezone, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()

# --- Constants ---

ICT_OFFSET = timedelta(hours=7)
PREDICTIONS_DIR = "predictions"
PSI_API_URL = os.getenv("PSI_API_URL", "https://api.psi-engine.dev/v1/predict")
PSI_API_KEY = os.getenv("PSI_ENGINE_API_KEY")
if PSI_API_KEY:
    print(f"[DEBUG] PSI_API_KEY loaded: {PSI_API_KEY[:3]}...")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
REGIME_TAXONOMY_URL = (
    "https://raw.githubusercontent.com/virachai/set-psi-validation"
    "/main/docs/010-regime-taxonomy-v01.json"
)

VALID_REGIMES = ["Bullish", "Bearish", "Sideways", "Risk-Off", "Crisis"]


# --- Domain Logic ---


def fetch_prediction() -> dict:
    """Calls the PSI Engine API and returns the raw prediction response."""
    if not PSI_API_KEY:
        print("[SKIP] PSI_ENGINE_API_KEY not set. Skipping prediction capture.")
        return {}

    headers = {
        "Accept": "application/json",
    }

    if RAPIDAPI_HOST:
        headers["x-rapidapi-host"] = RAPIDAPI_HOST
        headers["x-rapidapi-key"] = PSI_API_KEY
    else:
        headers["Authorization"] = f"Bearer {PSI_API_KEY}"

    print(f"[FETCH] Requesting prediction from {PSI_API_URL}...")
    with httpx.Client(timeout=30.0) as client:
        response = client.get(PSI_API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"[FETCH] Response received: {json.dumps(data, indent=2)}")
        return data


def build_snapshot(raw: dict, session: str = "full_day") -> dict:
    """Transforms raw API response into schema.org-compliant Observation.

    Handles two formats:
    1. Native schema.org response (Lambda) — passthrough with backward-compat fields added.
    2. Legacy RapidAPI format ({status, data: {regime, psi, ...}}) — full transform.
    """
    if not isinstance(raw, dict):
        return {}

    # Detect native schema.org response from our Lambda
    if raw.get("@type") == "Observation":
        obs = dict(raw)
        now_ict = datetime.now(timezone.utc) + ICT_OFFSET
        ts = obs.get("observationDate", now_ict.strftime("%Y-%m-%dT%H:%M:%S+07:00"))
        date_str = now_ict.strftime("%Y-%m-%d")
        regime = "Unclassified"
        psi_score = 0.0
        for pv in obs.get("variableMeasured", []):
            if pv.get("name") == "Predicted Regime":
                regime = pv.get("value", regime)
            elif pv.get("name") == "PSI Score":
                psi_score = pv.get("value", psi_score)
        # Backward-compat fields
        obs["timestamp"] = ts
        obs["date"] = date_str
        obs["predictedRegime"] = regime
        obs["psiScore"] = psi_score
        obs["modelId"] = "PSI Engine v1 (Lambda)"
        obs["session"] = session
        # Normalise regime naming
        regime_map = {}
        for r in VALID_REGIMES:
            key = r.upper().replace("-", "").replace("_", "")
            regime_map[key] = r
        clean = regime.upper().replace("-", "").replace("_", "")
        obs["predictedRegime"] = regime_map.get(clean, regime)
        return obs

    # Legacy: unwrap nested data payload
    payload = raw.get("data") if isinstance(raw.get("data"), dict) else raw  # type: ignore[union-attr]

    raw_regime = payload.get("regime") or payload.get("predictedRegime") or "Unclassified"  # type: ignore[union-attr]
    # Normalise case and separators: "SIDEWAYS" → "Sideways", "RISK_OFF" → "Risk-Off"
    regime_map = {}
    for r in VALID_REGIMES:
        key = r.upper().replace("-", "").replace("_", "")
        regime_map[key] = r
    clean = raw_regime.upper().replace("-", "").replace("_", "")
    predicted_regime = regime_map.get(clean, raw_regime)
    psi_score = payload.get("psi") or payload.get("psiScore") or 0.0  # type: ignore[union-attr]
    model_id = payload.get("modelId") or payload.get("model_id") or "PSI Engine v1"  # type: ignore[union-attr]

    if predicted_regime not in VALID_REGIMES:
        print(f"[WARN] Unknown regime '{predicted_regime}' from API.")

    now_ict = datetime.now(timezone.utc) + ICT_OFFSET
    date_str = now_ict.strftime("%Y-%m-%d")
    timestamp_iso = now_ict.strftime("%Y-%m-%dT%H:%M:%S+07:00")

    return {
        "@context": "https://schema.org",
        "@type": "Observation",
        "name": f"PSI Prediction {date_str}",
        "observationDate": timestamp_iso,
        "measuredProperty": {
            "@type": "DefinedTerm",
            "name": "Predicted Regime",
            "inDefinedTermSet": REGIME_TAXONOMY_URL,
        },
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "name": "PSI Score",
                "value": psi_score,
                "minValue": 0,
                "maxValue": 1,
            },
            {
                "@type": "PropertyValue",
                "name": "Predicted Regime",
                "value": predicted_regime,
            },
        ],
        "measurementMethod": {
            "@type": "DefinedTerm",
            "name": model_id,
        },
        # --- original fields preserved for backward compatibility ---
        "timestamp": timestamp_iso,
        "date": date_str,
        "predictedRegime": predicted_regime,
        "psiScore": psi_score,
        "modelId": model_id,
        "session": session,
    }


def save_snapshot(snapshot: dict) -> str:
    """Writes the prediction snapshot to predictions/YYYY-MM-DD-HHMMSS-session.json."""
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)

    # Use timestamp from the snapshot or generate now
    ts_str = snapshot.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
    # Format to YYYY-MM-DD-HHMMSS
    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).strftime("%Y-%m-%d-%H%M%S")
    session = snapshot.get("session", "full_day")

    filepath = os.path.join(PREDICTIONS_DIR, f"{dt}-{session}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"[SAVE] Prediction written to {filepath}")
    return filepath


# --- Entry Point ---


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="PSI Prediction Loader")
    parser.add_argument(
        "--session",
        choices=["am", "pm", "full_day"],
        default="full_day",
        help="Prediction session window (am, pm, full_day).",
    )
    args = parser.parse_args()

    try:
        data = fetch_prediction()
        if not data:
            return
        snapshot = build_snapshot(data, session=args.session)
        save_snapshot(snapshot)
        print("[DONE] Prediction capture complete.")
    except httpx.HTTPStatusError as e:
        if e.response.status_code in [401, 403]:
            print(f"[SKIP] API Authentication failed ({e.response.status_code}). Check secrets.")
            return
        print(f"[ERROR] API returned {e.response.status_code}: {e.response.text}")
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"[ERROR] Network error contacting PSI Engine: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Prediction capture failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
