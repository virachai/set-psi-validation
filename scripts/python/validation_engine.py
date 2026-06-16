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
import glob
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from utils import log_event, log_failure

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
    
    msg = f"Written to {filepath}"
    print(f"[SAVE] {msg}")
    log_event("INFO", "validation_engine", msg)


# --- Engine Actions ---


def find_latest_file(directory: str, date_str: str) -> Optional[str]:
    """Finds the latest file matching YYYY-MM-DD-*.json."""
    files = glob.glob(os.path.join(directory, f"{date_str}-*.json"))
    if not files:
        # Fallback to legacy YYYY-MM-DD.json
        legacy = os.path.join(directory, f"{date_str}.json")
        return legacy if os.path.exists(legacy) else None
    return max(files, key=os.path.getmtime)


def find_latest_prediction_file(directory: str, date_str: str, session: str) -> Optional[str]:
    """Finds the latest prediction file matching YYYY-MM-DD-*-session.json."""
    files = glob.glob(os.path.join(directory, f"{date_str}-*-{session}.json"))
    if not files:
        # Fallback to check if the file matches YYYY-MM-DD-*.json and has matching "session" field
        all_files = glob.glob(os.path.join(directory, f"{date_str}-*.json"))
        matching = []
        for f in all_files:
            # Avoid matching files that explicitly have a different suffix
            if not f.endswith(f"-{session}.json") and any(
                f.endswith(f"-{s}.json") for s in ["am", "pm", "full_day"]
            ):
                continue
            data = load_json(f)
            if data and data.get("session") == session:
                matching.append(f)
        return max(matching, key=os.path.getmtime) if matching else None
    return max(files, key=os.path.getmtime)


def run_daily_validation(date_str: str) -> list[Dict[str, Any]]:
    """Performs validation for a single date across all 3 windows (am, pm, full_day)."""
    market_path = find_latest_file(MARKET_DATA_DIR, date_str)
    if not market_path:
        msg = f"Missing market data path for {date_str}"
        print(f"[SKIP] {msg}")
        log_event("WARN", "validation_engine", msg)
        return []

    market = load_json(market_path)
    if not market:
        msg = f"Missing market data for {date_str}"
        print(f"[SKIP] {msg}")
        log_event("WARN", "validation_engine", msg)
        return []

    # Extract regimes (handle both schema.org and flat formats)
    actual_regime = market.get("actualRegime")
    if not actual_regime and "variableMeasured" in market:
        for vm in market["variableMeasured"]:
            if vm.get("name") == "Actual Regime":
                actual_regime = vm.get("value")

    if not actual_regime:
        msg = f"Could not extract actual regime for {date_str}"
        print(f"[ERROR] {msg}")
        log_event("ERROR", "validation_engine", msg)
        return []

    records = []
    # Loop over the 3 sessions
    for session in ["am", "pm", "full_day"]:
        pred_path = find_latest_prediction_file(PREDICTIONS_DIR, date_str, session)
        if not pred_path:
            # Fallback for full_day to also try the general latest file if no specific full_day exists
            if session == "full_day":
                pred_path = find_latest_file(PREDICTIONS_DIR, date_str)
                # But check that it doesn't belong to another session
                if pred_path:
                    p_data = load_json(pred_path)
                    if p_data and p_data.get("session") in ["am", "pm"]:
                        pred_path = None
            if not pred_path:
                log_event("INFO", "validation_engine", f"No prediction for {date_str} ({session})")
                continue

        prediction = load_json(pred_path)
        if not prediction:
            log_event("WARN", "validation_engine", f"Missing prediction data for {date_str} ({session})")
            continue

        predicted_regime = prediction.get("predictedRegime")
        if not predicted_regime and "variableMeasured" in prediction:
            for vm in prediction["variableMeasured"]:
                if vm.get("name") == "Predicted Regime":
                    predicted_regime = vm.get("value")

        if not predicted_regime:
            log_event("ERROR", "validation_engine", f"Could not extract predicted regime from {pred_path}")
            continue

        is_correct = compare_regimes(predicted_regime, actual_regime)
        deviation = compute_deviation_score(predicted_regime, actual_regime)

        log_event("INFO", "validation_engine", f"Validated {date_str} ({session})", {
            "predicted": predicted_regime,
            "actual": actual_regime,
            "is_correct": is_correct
        })

        now_ict = datetime.now(timezone.utc) + ICT_OFFSET
        timestamp_iso = now_ict.strftime("%Y-%m-%dT%H:%M:%S+07:00")

        # Use prediction filename stem for the validation record filename to support multiple snapshots
        pred_file_id = os.path.splitext(os.path.basename(pred_path))[0]
        validation_file_id = pred_file_id

        validation_record = {
            "@context": "https://schema.org",
            "@type": "Observation",
            "name": f"Validation Evaluation {validation_file_id}",
            "observationDate": timestamp_iso,
            "observationAbout": [
                {"@id": f"predictions/{os.path.basename(pred_path)}"},
                {"@id": f"market-data/{os.path.basename(market_path)}"},
            ],
            "measuredProperty": {"@type": "DefinedTerm", "name": "Regime Prediction Accuracy"},
            "variableMeasured": {
                "@type": "PropertyValue",
                "name": "Is Correct",
                "value": is_correct,
            },
            "marginOfError": {"@type": "QuantitativeValue", "value": deviation},
            # --- Internal fields ---
            "date": date_str,
            "file_id": validation_file_id,
            "session": session,
            "predictedRegime": predicted_regime,
            "actualRegime": actual_regime,
            "isCorrect": is_correct,
            "deviationScore": deviation,
        }

        save_json(os.path.join(VALIDATION_DIR, f"{validation_file_id}.json"), validation_record)
        records.append(validation_record)

    return records


def update_aggregate_metrics() -> None:
    """Scans validation/ directory and updates reports/metrics.json."""
    if not os.path.exists(VALIDATION_DIR):
        log_event("WARN", "validation_engine", "Validation directory does not exist.")
        return

    all_files = [f for f in os.listdir(VALIDATION_DIR) if f.endswith(".json")]
    records = []
    for f in sorted(all_files):
        data = load_json(os.path.join(VALIDATION_DIR, f))
        if data and "date" in data:
            records.append(
                {
                    "date": data["date"],
                    "file_id": data.get("file_id", data["date"]),
                    "session": data.get("session", "full_day"),
                    "predicted": data["predictedRegime"],
                    "actual": data["actualRegime"],
                    "correct": data["isCorrect"],
                }
            )

    if not records:
        log_event("WARN", "validation_engine", "No validation records found to aggregate.")
        return

    log_event("INFO", "validation_engine", f"Aggregating {len(records)} records...")

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

    # Calculate per-session metrics
    by_window = {}
    for s in ["am", "pm", "full_day"]:
        sdf = df[df["session"] == s]
        if not sdf.empty:
            s_acc = sdf["correct"].mean()
            s_7d = sdf["correct"].rolling(window=7, min_periods=1).mean().iloc[-1]
            s_30d = sdf["correct"].rolling(window=30, min_periods=1).mean().iloc[-1]
            by_window[s] = {
                "overall_accuracy": float(s_acc),
                "rolling_7d": float(s_7d),
                "rolling_30d": float(s_30d),
                "total_count": int(len(sdf)),
            }
        else:
            by_window[s] = {
                "overall_accuracy": 0.0,
                "rolling_7d": 0.0,
                "rolling_30d": 0.0,
                "total_count": 0,
            }

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
            "by_window": by_window,
            "hit_rates": hit_rates,
            "total_count": len(df),
        },
        "confusion_matrix": confusion.to_dict(),
        "history": df.tail(30)
        .assign(date=df["date"].dt.strftime("%Y-%m-%d"))
        .to_dict(orient="records"),
    }

    # Generate timestamped filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report_filename = f"metrics-{timestamp}.json"
    save_json(os.path.join(REPORTS_DIR, report_filename), metrics_report)

    # Maintain a symlink/copy for the latest report for dashboard compatibility
    save_json(os.path.join(REPORTS_DIR, "metrics.json"), metrics_report)
    log_event("INFO", "validation_engine", "Metrics aggregation complete.")


# --- Main ---


def main() -> None:
    try:
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
            log_event("INFO", "validation_engine", "Recomputing all validations")
            # Extract YYYY-MM-DD from filenames like YYYY-MM-DD-HHMMSS.json or YYYY-MM-DD.json
            pred_dates = {
                os.path.splitext(f)[0][:10]
                for f in os.listdir(PREDICTIONS_DIR)
                if f.endswith(".json")
            }
            market_dates = {
                os.path.splitext(f)[0][:10]
                for f in os.listdir(MARKET_DATA_DIR)
                if f.endswith(".json")
            }
            common_dates = sorted(list(pred_dates.intersection(market_dates)))
            log_event("INFO", "validation_engine", f"Found {len(common_dates)} common dates for recomputation")
            for d in common_dates:
                run_daily_validation(d)
        else:
            date_str = args.date or (datetime.now(timezone.utc) + ICT_OFFSET).strftime("%Y-%m-%d")
            log_event("INFO", "validation_engine", f"Running validation for {date_str}")
            run_daily_validation(date_str)

        update_aggregate_metrics()
        print("[DONE] Validation engine execution complete.")
        log_event("INFO", "validation_engine", "Execution complete")
    except Exception as e:
        error_msg = f"Validation engine execution failed: {e}"
        log_failure("validation_engine", error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
