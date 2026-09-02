# /// script
# dependencies = ["pandas", "numpy"]
# ///
"""PSI Validation Engine (Phase 2).

Performs daily validation by comparing predictions vs. actual market outcomes.
Computes accuracy metrics, maintains rolling history, and generates reports.

Outputs:
  - validation/YYYY-MM-DD.json  : Individual daily evaluation.
  - reports/metrics.json       : Aggregated rolling metrics & confusion matrix.

Governance: Compliant with "Lean PSI Validator" principles.
"""

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from utils import log_event, log_failure

# --- Constants ---

ICT_OFFSET = timedelta(hours=7)
PREDICTIONS_DIR = "predictions"
MARKET_DATA_DIR = "market-data"
VALIDATION_DIR = "validation"
REPORTS_DIR = "reports"

VALID_REGIMES = ["Bullish", "Bearish", "Sideways", "Risk-Off", "Crisis", "Unclassified"]

SESSIONS = ("am", "pm", "full_day")

# Regime derivation thresholds (mirrors capture_market.py)
BULLISH_MIN_RETURN = 0.005
CRISIS_RETURN = -0.02
DOWN_MOVE_MAX_RETURN = -0.005
SIDEWAYS_BAND = 0.005

# --- Core Logic ---


def derive_actual_regime(
    ato_price: float,
    atc_price: float,
    volatility_index: float,
    threshold_mean: float,
) -> str:
    """Derive the actual market regime based on intraday return and volatility.

    Matches logic in capture_market.py and docs/001-actual-regime-derivation-logic-v01.md.
    """
    return_pct = (atc_price - ato_price) / ato_price

    if return_pct > BULLISH_MIN_RETURN and volatility_index < threshold_mean:
        return "Bullish"
    if return_pct < CRISIS_RETURN and volatility_index >= (threshold_mean * 2):
        return "Crisis"
    if return_pct < DOWN_MOVE_MAX_RETURN and volatility_index > threshold_mean:
        return "Risk-Off"
    if return_pct < DOWN_MOVE_MAX_RETURN and volatility_index < threshold_mean:
        return "Bearish"
    if abs(return_pct) <= SIDEWAYS_BAND and volatility_index < threshold_mean:
        # Note: SIDEWAYS_BAND is inclusive for Sideways
        return "Sideways"
    return "Unclassified"


def compare_regimes(predicted: str, actual: str) -> bool:
    """Return True if the prediction matches the actual outcome."""
    return predicted == actual


def compute_deviation_score(predicted: str, actual: str) -> float:
    """Compute a simple deviation score.

    0.0 = perfect match.
    1.0 = mismatch.
    (Future: could be weighted based on regime proximity).
    """
    return 0.0 if predicted == actual else 1.0


# --- File I/O ---


def load_json(filepath: str) -> dict[str, Any] | None:
    """Load a JSON file, returning None when it is missing or empty."""
    path = Path(filepath)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: object) -> None:
    """Write data as pretty JSON to filepath, creating parent directories."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    msg = f"Written to {filepath}"
    print(f"[SAVE] {msg}")
    log_event("INFO", "validation_engine", msg)


# --- Engine Actions ---


def find_latest_file(directory: str, date_str: str) -> str | None:
    """Find the latest file matching YYYY-MM-DD-*.json."""
    files = sorted(Path(directory).glob(f"{date_str}-*.json"))
    if not files:
        # Fallback to legacy YYYY-MM-DD.json
        legacy = Path(directory) / f"{date_str}.json"
        return str(legacy) if legacy.exists() else None
    return str(files[-1])


def find_latest_market_file(directory: str, date_str: str) -> str | None:
    """Find the latest completed market data file (preferring *-atc.json)."""
    market_dir = Path(directory)
    # 1. Prefer completed ATC file: {date_str}-*-atc.json
    atc_files = sorted(market_dir.glob(f"{date_str}-*-atc.json"))
    if atc_files:
        return str(atc_files[-1])

    # 2. Check general {date_str}-*.json for completed status or actualRegime
    # (excluding explicit *-ato.json files)
    all_files = sorted(market_dir.glob(f"{date_str}-*.json"))
    for f in reversed(all_files):
        if f.name.endswith("-ato.json"):
            continue
        data = load_json(str(f))
        if data and (
            _extract_regime_value(data, "actualRegime", "Actual Regime")
            or data.get("status") == "complete"
        ):
            return str(f)

    # 3. Fallback to legacy YYYY-MM-DD.json
    legacy = market_dir / f"{date_str}.json"
    if legacy.exists():
        data = load_json(str(legacy))
        if data and _extract_regime_value(data, "actualRegime", "Actual Regime"):
            return str(legacy)

    return None


def find_latest_prediction_file(directory: str, date_str: str, session: str) -> str | None:
    """Find the latest prediction file matching YYYY-MM-DD-*-session.json."""
    files = sorted(Path(directory).glob(f"{date_str}-*-{session}.json"))
    if files:
        return str(files[-1])

    # Fallback: general YYYY-MM-DD-*.json files whose content declares the session
    matching = []
    all_files = sorted(Path(directory).glob(f"{date_str}-*.json"))
    for f in all_files:
        # Avoid files that explicitly carry a different session suffix
        if not f.name.endswith(f"-{session}.json") and any(
            f.name.endswith(f"-{s}.json") for s in SESSIONS
        ):
            continue
        data = load_json(str(f))
        if data and data.get("session") == session:
            matching.append(f)
    if not matching:
        return None
    return str(max(matching, key=lambda p: p.stat().st_mtime))


def _extract_regime_value(observation: dict, flat_key: str, measure_name: str) -> str | None:
    """Return a regime from a flat field or schema.org variableMeasured list."""
    value = observation.get(flat_key)
    if value:
        return value
    for vm in observation.get("variableMeasured", []):
        if isinstance(vm, dict) and vm.get("name") == measure_name:
            return vm.get("value")
    return None


def _resolve_prediction_path(date_str: str, session: str) -> str | None:
    """Resolve the prediction file for a session, with full_day fallbacks."""
    pred_path = find_latest_prediction_file(PREDICTIONS_DIR, date_str, session)
    if pred_path:
        return pred_path

    # Fallback for full_day: general latest file, unless owned by another session
    if session != "full_day":
        return None
    pred_path = find_latest_file(PREDICTIONS_DIR, date_str)
    if pred_path:
        p_data = load_json(pred_path)
        if p_data and p_data.get("session") in ["am", "pm"]:
            return None
    return pred_path


def _build_validation_record(
    date_str: str,
    session: str,
    pred_path: str,
    market_path: str,
    regimes: tuple[str, str],
) -> dict[str, Any]:
    """Build the schema.org Observation record for one validated session.

    regimes: (predicted_regime, actual_regime) tuple.
    """
    predicted_regime, actual_regime = regimes
    is_correct = compare_regimes(predicted_regime, actual_regime)
    deviation = compute_deviation_score(predicted_regime, actual_regime)

    log_event(
        "INFO",
        "validation_engine",
        f"Validated {date_str} ({session})",
        {"predicted": predicted_regime, "actual": actual_regime, "is_correct": is_correct},
    )

    now_ict = datetime.now(UTC) + ICT_OFFSET
    timestamp_iso = now_ict.strftime("%Y-%m-%dT%H:%M:%S+07:00")

    # Use the prediction filename stem for the validation record filename
    # so multiple snapshots per day stay distinct
    validation_file_id = Path(pred_path).stem

    return {
        "@context": "https://schema.org",
        "@type": "Observation",
        "name": f"Validation Evaluation {validation_file_id}",
        "observationDate": timestamp_iso,
        "observationAbout": [
            {"@id": f"predictions/{Path(pred_path).name}"},
            {"@id": f"market-data/{Path(market_path).name}"},
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


def run_daily_validation(date_str: str) -> list[dict[str, Any]]:
    """Validate a single date across all 3 windows (am, pm, full_day)."""
    market_path = find_latest_market_file(MARKET_DATA_DIR, date_str)
    if not market_path:
        msg = f"Missing complete market data path for {date_str}"
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
    actual_regime = _extract_regime_value(market, "actualRegime", "Actual Regime")
    if not actual_regime:
        msg = f"Could not extract actual regime for {date_str}"
        print(f"[ERROR] {msg}")
        log_event("ERROR", "validation_engine", msg)
        return []

    records = []
    # Loop over the 3 sessions
    for session in SESSIONS:
        pred_path = _resolve_prediction_path(date_str, session)
        if not pred_path:
            log_event("INFO", "validation_engine", f"No prediction for {date_str} ({session})")
            continue

        prediction = load_json(pred_path)
        if not prediction:
            log_event(
                "WARN",
                "validation_engine",
                f"Missing prediction data for {date_str} ({session})",
            )
            continue

        predicted_regime = _extract_regime_value(
            prediction,
            "predictedRegime",
            "Predicted Regime",
        )
        if not predicted_regime:
            msg = f"Could not extract predicted regime from {pred_path}"
            log_event("ERROR", "validation_engine", msg)
            continue

        record = _build_validation_record(
            date_str,
            session,
            pred_path,
            market_path,
            (predicted_regime, actual_regime),
        )
        save_json(str(Path(VALIDATION_DIR) / f"{record['file_id']}.json"), record)
        records.append(record)

    return records


def prune_orphan_validations() -> int:
    """Remove validation records that reference non-existent prediction files."""
    validation_dir = Path(VALIDATION_DIR)
    if not validation_dir.exists():
        return 0

    pruned = 0
    for f in sorted(validation_dir.glob("*.json")):
        data = load_json(str(f))
        if not data or not isinstance(data, dict):
            continue

        pred_id = None
        for about in data.get("observationAbout", []):
            if isinstance(about, dict) and about.get("@id", "").startswith("predictions/"):
                pred_id = about.get("@id")
                break

        if pred_id:
            pred_filename = Path(pred_id).name
            pred_file = Path(PREDICTIONS_DIR) / pred_filename
            if not pred_file.exists():
                print(f"[PRUNE] Removing orphan validation file {f.name} (missing {pred_file})")
                log_event("INFO", "validation_engine", f"Pruning orphan validation file {f.name}")
                f.unlink(missing_ok=True)
                pruned += 1
    return pruned


def update_aggregate_metrics() -> None:
    """Scan the validation/ directory and update reports/metrics.json."""
    validation_dir = Path(VALIDATION_DIR)
    if not validation_dir.exists():
        log_event("WARN", "validation_engine", "Validation directory does not exist.")
        return

    records = []
    for f in sorted(validation_dir.iterdir()):
        if f.suffix != ".json":
            continue
        data = load_json(str(f))
        if data and "date" in data:
            records.append(
                {
                    "date": data["date"],
                    "file_id": data.get("file_id", data["date"]),
                    "session": data.get("session", "full_day"),
                    "predicted": data["predictedRegime"],
                    "actual": data["actualRegime"],
                    "correct": data["isCorrect"],
                },
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
    pred_cat = pd.Categorical(df["predicted"], categories=VALID_REGIMES)
    actual_cat = pd.Categorical(df["actual"], categories=VALID_REGIMES)
    confusion = pd.crosstab(
        pred_cat,
        actual_cat,
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
    for s in SESSIONS:
        sdf = df[df["session"] == s]
        if not sdf.empty:
            s_acc = sdf["correct"].mean()
            s_7d = sdf["correct"].rolling(window=7, min_periods=1).mean().iloc[-1]
            s_30d = sdf["correct"].rolling(window=30, min_periods=1).mean().iloc[-1]
            by_window[s] = {
                "overall_accuracy": float(s_acc),
                "rolling_7d": float(s_7d),
                "rolling_30d": float(s_30d),
                "total_count": len(sdf),
            }
        else:
            by_window[s] = {
                "overall_accuracy": 0.0,
                "rolling_7d": 0.0,
                "rolling_30d": 0.0,
                "total_count": 0,
            }

    now_ict = datetime.now(UTC) + ICT_OFFSET
    metrics_report = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "PSI Aggregated Metrics",
        "description": "Rolling performance metrics for PSI regime validation.",
        "measuredProperty": {"@type": "DefinedTerm", "name": "Regime Prediction Accuracy"},
        "datePublished": now_ict.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
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

    # Timestamped copy, named like market-data/predictions: {YYYY-MM-DD}-{HHMMSS}-metrics.json
    report_filename = now_ict.strftime("%Y-%m-%d-%H%M%S-metrics.json")
    reports_dir = Path(REPORTS_DIR)
    save_json(str(reports_dir / report_filename), metrics_report)

    # Maintain a symlink/copy for the latest report for dashboard compatibility
    save_json(str(reports_dir / "metrics.json"), metrics_report)
    log_event("INFO", "validation_engine", "Metrics aggregation complete.")


def _dates_in_dir(directory: str) -> set[str]:
    """Return the set of YYYY-MM-DD prefixes present among JSON files."""
    return {f.name[:10] for f in Path(directory).iterdir() if f.suffix == ".json"}


# --- Main ---


def main() -> None:
    """Run validation for one date (or all common dates) and refresh metrics."""
    try:
        parser = argparse.ArgumentParser(description="PSI Validation Engine")
        parser.add_argument("--date", help="Date to validate (YYYY-MM-DD). Defaults to today.")
        parser.add_argument(
            "--recompute-all",
            action="store_true",
            help="Revalidate all dates with prediction & market data.",
        )
        args = parser.parse_args()

        prune_orphan_validations()

        if args.recompute_all:
            print("[INIT] Recomputing all validations...")
            log_event("INFO", "validation_engine", "Recomputing all validations")
            # Extract YYYY-MM-DD from filenames like YYYY-MM-DD-HHMMSS.json or YYYY-MM-DD.json
            pred_dates = _dates_in_dir(PREDICTIONS_DIR)
            market_dates = _dates_in_dir(MARKET_DATA_DIR)
            common_dates = sorted(pred_dates.intersection(market_dates))
            log_event(
                "INFO",
                "validation_engine",
                f"Found {len(common_dates)} common dates for recomputation",
            )
            for d in common_dates:
                run_daily_validation(d)
        else:
            date_str = args.date or (datetime.now(UTC) + ICT_OFFSET).strftime("%Y-%m-%d")
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
