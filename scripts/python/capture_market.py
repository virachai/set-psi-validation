# /// script
# dependencies = ["python-dotenv", "yfinance"]
# ///
"""Market Data Capture (Single Daily Cycle, ATO -> ATC).

Runs once after the SET close: fetches the day's opening (ATO) and closing (ATC)
prices from the provider in a single call, computes return/volatility, derives the
full-day actual regime, and saves a schema.org-compliant Observation JSON-LD file
(see RFC 020).

Modes:
  --mode atc     : The only mode (default).

Output: market-data/YYYY-MM-DD-HHMMSS-{mode}.json

Governance: Compliant with "Lean PSI Validator" principles.
"""

import argparse
import json
import os
import sys
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from dotenv import load_dotenv
from providers import fetch_yahoo_ato_open, fetch_yahoo_quote
from regime_rules import DEFAULT_THRESHOLD_MEAN, VALID_REGIMES, derive_actual_regime
from utils import log_event, log_failure

load_dotenv()

# --- Constants ---

ICT_OFFSET = timedelta(hours=7)
MARKET_DATA_DIR = "market-data"
REGIME_TAXONOMY_URL = (
    "https://raw.githubusercontent.com/virachai/set-psi-validation"
    "/main/docs/010-regime-taxonomy-v01.json"
)

SET_MARKET_CLOSE_ICT = time(16, 30)

# The ICT wall-clock window during which a mode's quote is a truthful stand-in for
# the snapshot it claims to be. `atc` reads the post-close price, which stays correct
# for the rest of the day, so it only needs a lower bound (cutoff `None`).
CAPTURE_WINDOWS: dict[str, tuple[time, time | None]] = {
    "atc": (SET_MARKET_CLOSE_ICT, None),
}
MAX_INTRADAY_VOLATILITY = 0.05
THRESHOLD_ROLLING_WINDOW_DAYS = 30
THRESHOLD_MIN_HISTORY_DAYS = 5  # below this, historical mean is too noisy — use the static default

# --- I/O Helpers ---


def save_market_data(
    record: dict,
    date_str: str,
    mode: str,
    captured_at: time | None = None,
) -> str:
    """Write the market data record to market-data/YYYY-MM-DD-HHMMSS-mode.json.

    Writes to a temp file in the same directory and atomically renames it into
    place, so a crash or interrupted write can never leave a partially-written
    or truncated JSON file behind.

    `captured_at` overrides the ICT wall-clock stamp in the filename. A live
    capture leaves it None (now is the capture time); a historical backfill
    passes the window time the price actually belongs to, so the filename keeps
    telling the truth about when the observation was taken.
    """
    market_dir = Path(MARKET_DATA_DIR)
    market_dir.mkdir(exist_ok=True)

    # Use date_str and the capture's ICT time (now, unless explicitly given)
    time_str = (captured_at or (datetime.now(UTC) + ICT_OFFSET).time()).strftime("%H%M%S")
    dt = f"{date_str}-{time_str}"

    filepath = market_dir / f"{dt}-{mode}.json"
    tmp_path = filepath.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    tmp_path.replace(filepath)

    msg = f"Market data written to {filepath}"
    print(f"[SAVE] {msg}")
    log_event("INFO", "capture_market", msg, {"date": date_str, "status": record.get("status")})
    return str(filepath)


def compute_rolling_threshold_mean(
    date_str: str,
    window_days: int = THRESHOLD_ROLLING_WINDOW_DAYS,
) -> float:
    """Compute the volatility threshold mean from the trailing N days of history.

    Reads ``volatilityIndex`` out of each prior day's completed ATC record (one
    value per date, most recent file per date if several exist) and averages
    the most recent ``window_days`` of them. Falls back to
    ``DEFAULT_THRESHOLD_MEAN`` when there isn't enough history yet (a cold
    start, or fewer than THRESHOLD_MIN_HISTORY_DAYS prior days on record) —
    this keeps regime derivation deterministic and reproducible per the
    guardrails in docs/02_research_reports/001-actual-regime-derivation-logic-v01.md
    instead of silently classifying every day against the same static 2% bar.
    """
    market_dir = Path(MARKET_DATA_DIR)
    if not market_dir.exists():
        return DEFAULT_THRESHOLD_MEAN

    by_date: dict[str, tuple[str, float]] = {}
    for filepath in sorted(market_dir.glob("*-atc.json")):
        file_date = filepath.name[:10]  # YYYY-MM-DD prefix
        if file_date >= date_str:
            continue  # never look at today or the future — no lookahead
        try:
            with filepath.open(encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("status") != "complete":
            continue
        volatility = data.get("volatilityIndex")
        if volatility is None:
            continue
        # Keep only the latest file per date (glob is sorted, so later wins).
        by_date[file_date] = (filepath.name, float(volatility))

    if len(by_date) < THRESHOLD_MIN_HISTORY_DAYS:
        log_event(
            "INFO",
            "capture_market",
            f"Rolling threshold: only {len(by_date)} prior day(s) on record "
            f"(need {THRESHOLD_MIN_HISTORY_DAYS}) — using static default {DEFAULT_THRESHOLD_MEAN}.",
        )
        return DEFAULT_THRESHOLD_MEAN

    ordered_dates = sorted(by_date)[-window_days:]
    values = [by_date[d][1] for d in ordered_dates]
    rolling_mean = sum(values) / len(values)

    log_event(
        "INFO",
        "capture_market",
        f"Rolling threshold mean over {len(values)} day(s): {round(rolling_mean, 4)}",
        {"window_days": window_days, "sample_size": len(values)},
    )
    return rolling_mean


# --- Mode Handlers ---


def handle_atc(
    date_str: str,
    ato_price: float,
    atc_price: float,
    volatility_index: float,
    threshold_mean: float = DEFAULT_THRESHOLD_MEAN,
) -> dict:
    """Create or update a complete market outcome Observation."""
    if ato_price is None or ato_price <= 0:
        msg = (
            f"Invalid ATO price ({ato_price}) found for {date_str}. Cannot compute full-day return."
        )
        print(f"[FAIL] {msg}")
        log_failure("capture_market", msg)
        raise RuntimeError(msg)

    return_pct = round((atc_price - ato_price) / ato_price * 100, 2)
    actual_regime = derive_actual_regime(ato_price, atc_price, volatility_index, threshold_mean)

    log_event(
        "INFO",
        "capture_market",
        f"Handling ATC for {date_str}",
        {
            "ato_price": ato_price,
            "atc_price": atc_price,
            "return_pct": return_pct,
            "regime": actual_regime,
        },
    )

    period_start = f"{date_str}T10:00:00+07:00"
    period_end = f"{date_str}T16:30:00+07:00"

    variable_measured = [
        {
            "@type": "QuantitativeValue",
            "name": "ATO Price",
            "value": ato_price,
            "unitText": "SET Index Points",
        },
        {
            "@type": "QuantitativeValue",
            "name": "ATC Price",
            "value": atc_price,
            "unitText": "SET Index Points",
        },
        {
            "@type": "PropertyValue",
            "name": "Return %",
            "value": return_pct,
        },
        {
            "@type": "PropertyValue",
            "name": "Intraday Volatility",
            "value": volatility_index,
        },
        {
            "@type": "PropertyValue",
            "name": "Actual Regime",
            "value": (actual_regime if actual_regime in VALID_REGIMES else "Unclassified"),
        },
    ]

    return {
        "@context": "https://schema.org",
        "@type": "Observation",
        "name": f"SET Market Outcome {date_str}",
        "observationDate": date_str,
        "observationPeriod": f"{period_start}/{period_end}",
        "measuredProperty": {
            "@type": "DefinedTerm",
            "name": "Actual Regime",
            "inDefinedTermSet": REGIME_TAXONOMY_URL,
        },
        "variableMeasured": variable_measured,
        "date": date_str,
        "atoPrice": ato_price,
        "atcPrice": atc_price,
        "returnPct": return_pct,
        "volatilityIndex": volatility_index,
        "thresholdMeanUsed": threshold_mean,
        "actualRegime": actual_regime,
        "status": "complete",
    }


# --- Entry Point ---


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Capture SET Market Data (Single Cycle).")
    parser.add_argument(
        "--mode",
        choices=["atc"],
        default="atc",
        help="Capture mode.",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Market symbol to fetch (e.g., ^SET.BK). If omitted, manual mode is assumed.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["yahoo"],
        default="yahoo",
        help="Data provider to use if --symbol is provided (yahoo is the primary source).",
    )
    parser.add_argument(
        "--ato-price",
        type=float,
        help="Manual entry: The official opening price (ATO).",
    )
    parser.add_argument(
        "--atc-price",
        type=float,
        help="Manual entry: The official closing price (ATC).",
    )
    parser.add_argument(
        "--volatility",
        type=float,
        default=0.01,
        help="Manual entry: The intraday volatility (high-low)/mid.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override the rolling threshold mean. If omitted, computes from last 30 days.",
    )
    return parser


def _already_captured(date_str: str, mode: str) -> bool:
    """Return True (and log) if today's complete market data for this mode already exists."""
    for path in sorted(Path(MARKET_DATA_DIR).glob(f"{date_str}-*-{mode}.json")):
        with path.open(encoding="utf-8") as f:
            if json.load(f).get("status") == "complete":
                print(f"[SKIP] {mode.upper()} data for {date_str} already exists.")
                return True
    return False


def _fetch_yahoo_prices(symbol: str, date_str: str, mode: str) -> tuple[float, float, float]:
    """Fetch ATO (10:00 bar open), ATC (daily close) and volatility from Yahoo Finance."""
    log_event(
        "INFO",
        "capture_market",
        f"Starting Yahoo Finance fetch for {symbol}",
        {"mode": mode},
    )
    data = fetch_yahoo_quote(symbol)
    if not data or float(data.get("c", 0.0)) == 0.0:
        error_msg = f"Yahoo Finance returned no valid quote for {symbol} on {date_str}."
        log_event("ERROR", "capture_market", error_msg)
        raise RuntimeError(error_msg)
    if not data.get("o"):
        error_msg = f"Yahoo Finance returned no valid open price for {symbol} on {date_str}."
        log_event("ERROR", "capture_market", error_msg)
        raise RuntimeError(error_msg)
    if not data.get("h") or not data.get("l"):
        error_msg = f"Yahoo Finance returned no valid high/low price for {symbol} on {date_str}."
        log_event("ERROR", "capture_market", error_msg)
        raise RuntimeError(error_msg)
    ato_price = fetch_yahoo_ato_open(symbol, date_str)
    if not ato_price:
        error_msg = f"Yahoo Finance returned no 10:00 bar (ATO) for {symbol} on {date_str}."
        log_event("ERROR", "capture_market", error_msg)
        raise RuntimeError(error_msg)
    atc_price = float(data.get("c", 0.0))
    high_p = float(data.get("h", atc_price))
    low_p = float(data.get("l", ato_price))
    mid_price = (high_p + low_p) / 2
    volatility = round((high_p - low_p) / mid_price, 4) if mid_price > 0 else 0.01
    volatility = min(volatility, MAX_INTRADAY_VOLATILITY)
    if mode == "atc":
        log_event(
            "WARN",
            "capture_market",
            f"Yahoo Finance ATC is the daily bar close, not a verified auction print, "
            f"for {symbol} on {date_str}.",
        )
    print(f"[YAHOO] ATO={ato_price}, ATC={atc_price}, Vol={volatility}")
    return ato_price, atc_price, volatility


def _fetch_live_prices(
    provider: str,
    symbol: str,
    date_str: str,
    mode: str,
) -> tuple[float, float, float]:
    """Fetch ATO/ATC/volatility from the chosen provider, enforcing fail-closed integrity."""
    if provider == "yahoo":
        return _fetch_yahoo_prices(symbol, date_str, mode)

    error_msg = f"Unknown market data provider: {provider}"
    raise ValueError(error_msg)


def _resolve_threshold(args: argparse.Namespace, date_str: str) -> float:
    """Return the explicit --threshold if given, else the computed rolling mean."""
    if args.threshold is not None:
        return args.threshold
    return compute_rolling_threshold_mean(date_str)


def _assert_before_cutoff(mode: str, cutoff: time, now_ict: datetime | None = None) -> None:
    """Fail closed if called at/after `cutoff` ICT.

    `noon` and `pmopen` fetch a live "current price" quote as a stand-in for a
    specific point-in-time snapshot. A schedule that fires late (e.g. a delayed
    GitHub Actions cron) would otherwise silently record a later, wrong price
    under that snapshot's label instead of erroring.
    """
    if now_ict is None:
        now_ict = datetime.now(UTC) + ICT_OFFSET
    if now_ict.time() >= cutoff:
        msg = (
            f"{mode} capture attempted at {now_ict.strftime('%H:%M:%S')} ICT, "
            f"at/after the {cutoff} ICT cutoff — the live quote no longer reflects "
            f"the {mode} snapshot."
        )
        log_event("ERROR", "capture_market", msg)
        raise RuntimeError(msg)


def _mark_bypass(record: dict, *, bypassed: bool) -> dict:
    """Stamp a record produced outside its capture window, so backfills stay auditable."""
    if bypassed:
        record["windowGuardBypassed"] = True
    return record


def _assert_after_open(mode: str, open_time: time, now_ict: datetime | None = None) -> None:
    """Fail closed if called before `open_time` ICT.

    The mirror of `_assert_before_cutoff`. Without it, an early run (notably a
    manual `workflow_dispatch` firing every step at once in the morning) records
    a pre-window live quote under a later snapshot's label — e.g. a 09:28 quote
    saved as the 12:30 noon close — silently corrupting the truth layer.
    """
    if now_ict is None:
        now_ict = datetime.now(UTC) + ICT_OFFSET
    if now_ict.time() < open_time:
        msg = (
            f"{mode} capture attempted at {now_ict.strftime('%H:%M:%S')} ICT, "
            f"before the {open_time} ICT window opens — the live quote does not yet "
            f"reflect the {mode} snapshot."
        )
        log_event("ERROR", "capture_market", msg)
        raise RuntimeError(msg)


def _assert_in_window(mode: str, now_ict: datetime | None = None) -> bool:
    """Assert the current ICT time falls inside `mode`'s capture window.

    Returns True when the guard was bypassed via `PSI_BYPASS_WINDOW_GUARD`, so the
    caller can stamp the record as a backfill. Raises `RuntimeError` otherwise.
    """
    open_time, cutoff = CAPTURE_WINDOWS[mode]
    bypassed = os.getenv("PSI_BYPASS_WINDOW_GUARD", "false").lower() == "true"
    try:
        _assert_after_open(mode, open_time, now_ict)
        if cutoff is not None:
            _assert_before_cutoff(mode, cutoff, now_ict)
    except RuntimeError:
        if not bypassed:
            raise
        log_event(
            "WARNING",
            "capture_market",
            "PSI_BYPASS_WINDOW_GUARD is enabled — recording an out-of-window capture. "
            "This is strictly prohibited in production.",
            {"mode": mode},
        )
        return True
    return False


def _capture_atc(args: argparse.Namespace, parser: argparse.ArgumentParser, date_str: str) -> dict:
    """Resolve the ATO and ATC prices and build its record."""
    bypassed = _assert_in_window("atc")
    if args.symbol:
        ato_price, atc_price, volatility = _fetch_live_prices(
            args.provider,
            args.symbol,
            date_str,
            "atc",
        )
    else:
        if args.atc_price is None or args.ato_price is None:
            parser.error(
                "--ato-price and --atc-price are required for --mode atc (or use --symbol).",
            )
        log_event("INFO", "capture_market", "Starting manual price entry", {"mode": "atc"})
        ato_price = args.ato_price
        atc_price = args.atc_price
        volatility = args.volatility
    threshold = _resolve_threshold(args, date_str)
    return _mark_bypass(
        handle_atc(date_str, ato_price, atc_price, volatility, threshold),
        bypassed=bypassed,
    )


def main() -> None:
    """Capture ATC market data for today and persist the Observation."""
    parser = _build_parser()
    args = parser.parse_args()
    date_str = (datetime.now(UTC) + ICT_OFFSET).strftime("%Y-%m-%d")

    if _already_captured(date_str, args.mode):
        return

    try:
        record = _capture_atc(args, parser, date_str)
        save_market_data(record, date_str, args.mode)
        print(f"[DONE] Market {args.mode.upper()} capture complete.")
    except Exception as e:
        error_msg = f"Market capture failed: {e}"
        log_failure("capture_market", error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
