# /// script
# dependencies = ["pandas", "numpy"]
# ///
"""
PSI Validation Engine (Phase 2)

Performs daily validation by comparing predictions vs. actual market outcomes.
Computes accuracy metrics, maintains rolling history, and generates reports.

Outputs:
  - validation/YYYY-MM-DD.json  : Individual daily evaluation.
  - reports/metrics.json       : Aggregated rolling metrics & confusion matrix.

Governance: Compliant with "Lean PSI Validator" principles.
"""

import os
import json
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

import pandas as pd

# --- Constants ---

ICT_OFFSET = timedelta(hours=7)
PREDICTIONS_DIR = "predictions"
MARKET_DATA_DIR = "market-data"
VALIDATION_DIR = "validation"
REPORTS_DIR = "reports"

VALID_REGIMES = ["Bullish", "Bearish", "Sideways", "Risk-Off", "Crisis"]

# --- Core Logic ---


def derive_actual_regime(
    ato_price: float,
    atc_price: float,
    volatility_index: float,
    threshold_mean: float,
) -> str:
    """
    Derives the actual market regime based on intraday return and volatility.
    Matches logic in capture_market.py and docs/001-actual-regime-derivation-logic-v01.md.
    """
    return_pct = (atc_price - ato_price) / ato_price

    if return_pct > 0.005 and volatility_index < threshold_mean:
        return "Bullish"
    elif return_pct < -0.02 and volatility_index > (threshold_mean * 2):
        return "Crisis"
    elif return_pct < -0.005 and volatility_index > threshold_mean:
        return "Risk-Off"
    elif return_pct < -0.005 and volatility_index < threshold_mean:
        return "Bearish"
    elif abs(return_pct) <= 0.005 and volatility_index < threshold_mean:
        # Note: 0.005 is inclusive for Sideways
        return "Sideways"
    else:
        return "Unclassified"


def compare_regimes(predicted: str, actual: str) -> bool:
    """Returns True if prediction matches actual outcome."""
    return predicted == actual


def compute_deviation_score(predicted: str, actual: str) -> float:
    """
    Computes a simple deviation score.
    0.0 = perfect match.
    1.0 = mismatch.
    (Future: could be weighted based on regime proximity).
    """
    return 0.0 if predicted == actual else 1.0


# --- File I/O ---


def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: Any) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[SAVE] Written to {filepath}")


# --- Engine Actions ---


def run_daily_validation(date_str: str) -> Optional[Dict[str, Any]]:
    """Performs validation for a single date."""
    pred_path = os.path.join(PREDICTIONS_DIR, f"{date_str}.json")
    market_path = os.path.join(MARKET_DATA_DIR, f"{date_str}.json")

    prediction = load_json(pred_path)
    market = load_json(market_path)

    if not prediction or not market:
        print(
            f"[SKIP] Missing data for {date_str} (Pred: {bool(prediction)}, Market: {bool(market)})"
        )
        return None

    # Extract regimes (handle both schema.org and flat formats)
    predicted_regime = prediction.get("predictedRegime")
    if not predicted_regime and "variableMeasured" in prediction:
        for vm in prediction["variableMeasured"]:
            if vm.get("name") == "Predicted Regime":
                predicted_regime = vm.get("value")

    actual_regime = market.get("actualRegime")
    if not actual_regime and "variableMeasured" in market:
        for vm in market["variableMeasured"]:
            if vm.get("name") == "Actual Regime":
                actual_regime = vm.get("value")

    if not predicted_regime or not actual_regime:
        print(f"[ERROR] Could not extract regimes for {date_str}")
        return None

    is_correct = compare_regimes(predicted_regime, actual_regime)
    deviation = compute_deviation_score(predicted_regime, actual_regime)

    now_ict = datetime.now(timezone.utc) + ICT_OFFSET
    timestamp_iso = now_ict.strftime("%Y-%m-%dT%H:%M:%S+07:00")

    validation_record = {
        "@context": "https://schema.org",
        "@type": "Observation",
        "name": f"Validation Evaluation {date_str}",
        "observationDate": timestamp_iso,
        "observationAbout": [
            {"@id": f"predictions/{date_str}.json"},
            {"@id": f"market-data/{date_str}.json"},
        ],
        "measuredProperty": {"@type": "DefinedTerm", "name": "Regime Prediction Accuracy"},
        "variableMeasured": {"@type": "PropertyValue", "name": "Is Correct", "value": is_correct},
        "marginOfError": {"@type": "QuantitativeValue", "value": deviation},
        # --- Internal fields ---
        "date": date_str,
        "predictedRegime": predicted_regime,
        "actualRegime": actual_regime,
        "isCorrect": is_correct,
        "deviationScore": deviation,
    }

    save_json(os.path.join(VALIDATION_DIR, f"{date_str}.json"), validation_record)
    return validation_record


def update_aggregate_metrics() -> None:
    """Scans validation/ directory and updates reports/metrics.json."""
    all_files = [f for f in os.listdir(VALIDATION_DIR) if f.endswith(".json")]
    records = []
    for f in sorted(all_files):
        data = load_json(os.path.join(VALIDATION_DIR, f))
        if data and "date" in data:
            records.append(
                {
                    "date": data["date"],
                    "predicted": data["predictedRegime"],
                    "actual": data["actualRegime"],
                    "correct": data["isCorrect"],
                }
            )

    if not records:
        print("[WARN] No validation records found to aggregate.")
        return

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Overall Accuracy
    total_accuracy = df["correct"].mean()

    # Rolling Accuracy (7D, 30D)
    # We use min_periods=1 to handle early days
    df["rolling_7d"] = df["correct"].rolling(window=7, min_periods=1).mean()
    df["rolling_30d"] = df["correct"].rolling(window=30, min_periods=1).mean()

    # Confusion Matrix
    # Ensure all regimes are present in the matrix
    confusion = pd.crosstab(
        pd.Categorical(df["predicted"], categories=VALID_REGIMES),
        pd.Categorical(df["actual"], categories=VALID_REGIMES),
        dropna=False,
    )

    # Regime Hit Rates (Recall per regime)
    hit_rates = {}
    for regime in VALID_REGIMES:
        regime_actuals = df[df["actual"] == regime]
        if not regime_actuals.empty:
            hit_rates[regime] = regime_actuals["correct"].mean()
        else:
            hit_rates[regime] = None

    metrics_report = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "PSI Aggregated Metrics",
        "description": "Rolling performance metrics for PSI regime validation.",
        "datePublished": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+07:00"),
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "name": "Overall Accuracy",
                "value": round(float(total_accuracy), 4),
            },
            {
                "@type": "PropertyValue",
                "name": "Rolling 7D Accuracy",
                "value": round(float(df["rolling_7d"].iloc[-1]), 4),
            },
            {
                "@type": "PropertyValue",
                "name": "Rolling 30D Accuracy",
                "value": round(float(df["rolling_30d"].iloc[-1]), 4),
            },
        ],
        "metrics": {
            "overall_accuracy": float(total_accuracy),
            "rolling_7d": float(df["rolling_7d"].iloc[-1]),
            "rolling_30d": float(df["rolling_30d"].iloc[-1]),
            "hit_rates": hit_rates,
            "total_count": len(df),
        },
        "confusion_matrix": confusion.to_dict(),
        "history": df.tail(30)
        .assign(date=df["date"].dt.strftime("%Y-%m-%d"))
        .to_dict(orient="records"),
    }

    save_json(os.path.join(REPORTS_DIR, "metrics.json"), metrics_report)


# --- Main ---


def main() -> None:
    parser = argparse.ArgumentParser(description="PSI Validation Engine")
    parser.add_argument("--date", help="Date to validate (YYYY-MM-DD). Defaults to today.")
    parser.add_argument(
        "--recompute-all",
        action="store_true",
        help="Revalidate all dates with prediction & market data.",
    )
    args = parser.parse_args()

    if args.recompute_all:
        print("[INIT] Recomputing all validations...")
        pred_dates = {f.split(".")[0] for f in os.listdir(PREDICTIONS_DIR) if f.endswith(".json")}
        market_dates = {f.split(".")[0] for f in os.listdir(MARKET_DATA_DIR) if f.endswith(".json")}
        common_dates = sorted(list(pred_dates.intersection(market_dates)))
        for d in common_dates:
            run_daily_validation(d)
    else:
        date_str = args.date or (datetime.now(timezone.utc) + ICT_OFFSET).strftime("%Y-%m-%d")
        run_daily_validation(date_str)

    update_aggregate_metrics()
    print("[DONE] Validation engine execution complete.")


if __name__ == "__main__":
    main()
