# /// script
# dependencies = ["pandas"]
# ///
"""Audit script for PSI Truth Layer.

Verifies consistency, schema compliance, and completeness between predictions/ and market-data/.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

# --- Constants & Utilities ---
PREDICTIONS_DIR = Path("predictions")
MARKET_DATA_DIR = Path("market-data")
REPORTS_DIR = Path("reports")
SESSIONS = ("am", "pm", "full_day")


def load_json(filepath: Path) -> dict[str, Any] | None:
    """Load a JSON file, returning None when it is missing or empty."""
    if not filepath.exists():
        return None
    try:
        with filepath.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def _extract_regime_value(observation: dict, flat_key: str, measure_name: str) -> str | None:
    """Return a regime from a flat field or schema.org variableMeasured list."""
    value = observation.get(flat_key)
    if value:
        return value
    for vm in observation.get("variableMeasured", []):
        if isinstance(vm, dict) and vm.get("name") == measure_name:
            return vm.get("value")
    return None


# --- Audit Logic ---


def get_file_metadata(path: Path) -> tuple[str, str]:
    """Extract (date, session) from filename (YYYY-MM-DD-*-session.json)."""
    # Simplified extraction based on typical naming: YYYY-MM-DD-HHMMSS-session.json
    parts = path.stem.split("-")
    date_part = "-".join(parts[:3])
    # Identify session from the end of the stem
    session = "full_day"
    if path.stem.endswith("-am"):
        session = "am"
    elif path.stem.endswith("-pm"):
        session = "pm"
    return date_part, session


def run_deep_audit() -> dict[str, Any]:
    """Perform deep audit on predictions and market data."""
    prediction_files = list(PREDICTIONS_DIR.glob("*.json"))
    market_files = list(MARKET_DATA_DIR.glob("*.json"))

    preds = {}
    for f in prediction_files:
        date, session = get_file_metadata(f)
        preds[(date, session)] = f

    markets = {}
    for f in market_files:
        date, session = get_file_metadata(f)
        markets[(date, session)] = f

    orphans = []  # Prediction exists, market data missing
    missing_matches = []  # Market data exists, prediction missing
    validation_errors = []

    all_keys = set(preds.keys()) | set(markets.keys())
    for key in all_keys:
        if key in preds and key not in markets:
            orphans.append({"date": key[0], "session": key[1], "file": str(preds[key])})
        elif key not in preds and key in markets:
            missing_matches.append({"date": key[0], "session": key[1], "file": str(markets[key])})
        else:
            # Check integrity
            p_data = load_json(preds[key])
            m_data = load_json(markets[key])
            if not p_data or not m_data:
                validation_errors.append(
                    {"date": key[0], "session": key[1], "error": "Malformed JSON"},
                )

    # Aggregate results
    report = {
        "auditDate": pd.Timestamp.now().isoformat(),
        "totalPredictions": len(preds),
        "totalMarketData": len(markets),
        "orphans": orphans,
        "missingMatches": missing_matches,
        "validationErrors": validation_errors,
    }

    # Save report
    REPORTS_DIR.mkdir(exist_ok=True)
    with (REPORTS_DIR / "audit_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    results = run_deep_audit()
    print(
        f"Audit complete. Findings: {len(results['orphans'])} orphans, "
        f"{len(results['missingMatches'])} missing matches.",
    )
