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
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

# --- Constants ---

ICT_OFFSET = timedelta(hours=7)
PREDICTIONS_DIR = "predictions"
PSI_API_URL = os.getenv("PSI_API_URL", "https://api.psi-engine.dev/v1/predict")
PSI_API_KEY = os.getenv("PSI_ENGINE_API_KEY")
REGIME_TAXONOMY_URL = (
    "https://raw.githubusercontent.com/user/set-psi-validation"
    "/main/docs/regime-taxonomy.jsonld"
)

VALID_REGIMES = ["Bullish", "Bearish", "Sideways", "Risk-Off", "Crisis"]


# --- Domain Logic ---


def fetch_prediction() -> dict:
    """Calls the PSI Engine API and returns the raw prediction response."""
    if not PSI_API_KEY:
        raise EnvironmentError(
            "PSI_ENGINE_API_KEY environment variable is not set."
        )

    headers = {
        "Authorization": f"Bearer {PSI_API_KEY}",
        "Accept": "application/json",
    }

    print(f"[FETCH] Requesting prediction from {PSI_API_URL}...")
    with httpx.Client(timeout=30.0) as client:
        response = client.get(PSI_API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"[FETCH] Response received: {json.dumps(data, indent=2)}")
        return data


def build_snapshot(data: dict) -> dict:
    """Transforms raw API response into schema.org-compliant Observation."""
    predicted_regime = data.get("predictedRegime", "Unclassified")
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
                "value": data.get("psiScore", 0.0),
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
            "name": data.get("modelId", "PSI Engine v1"),
        },
        # --- original fields preserved for backward compatibility ---
        "timestamp": timestamp_iso,
        "date": date_str,
        "predictedRegime": predicted_regime,
        "psiScore": data.get("psiScore", 0.0),
        "modelId": data.get("modelId", "PSI Engine v1"),
    }


def save_snapshot(snapshot: dict) -> str:
    """Writes the prediction snapshot to predictions/YYYY-MM-DD.json."""
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    date_str = snapshot["date"]
    filepath = os.path.join(PREDICTIONS_DIR, f"{date_str}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"[SAVE] Prediction written to {filepath}")
    return filepath


# --- Entry Point ---


def main() -> None:
    try:
        data = fetch_prediction()
        snapshot = build_snapshot(data)
        save_snapshot(snapshot)
        print("[DONE] Prediction capture complete.")
    except httpx.HTTPStatusError as e:
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
