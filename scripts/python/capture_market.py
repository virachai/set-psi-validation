# /// script
# dependencies = ["python-dotenv", "httpx", "yfinance"]
# ///
"""Market Data Capture (ATO / ATC).

Captures SET market open (ATO) and close (ATC) data, computes intraday metrics,
derives the actual regime, and saves as a schema.org-compliant Observation JSON-LD file.

Modes:
  --mode ato   : Capture opening price (partial record, awaits ATC).
  --mode atc   : Capture closing price, compute return/volatility, derive regime.

Output: market-data/YYYY-MM-DD.json

Governance: Compliant with "Lean PSI Validator" principles.
"""

import argparse
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from dotenv import load_dotenv
from providers import fetch_finnhub_quote, fetch_yahoo_quote
from regime_rules import VALID_REGIMES, derive_actual_regime
from utils import log_event, log_failure

load_dotenv()

# --- Constants ---

ICT_OFFSET = timedelta(hours=7)
MARKET_DATA_DIR = "market-data"
REGIME_TAXONOMY_URL = (
    "https://raw.githubusercontent.com/virachai/set-psi-validation"
    "/main/docs/010-regime-taxonomy-v01.json"
)

MAX_INTRADAY_VOLATILITY = 0.05
MASK_KEY_MIN_LENGTH = 6  # longer keys show first/last 3 chars

# --- SETSMART API ---

SETSMART_BASE_URL = "https://www.setsmart.com"
SETSMART_API_KEY = os.getenv("SETSMART_API_KEY")
if SETSMART_API_KEY:
    masked_key = (
        f"{SETSMART_API_KEY[:3]}***{SETSMART_API_KEY[-3:]}"
        if len(SETSMART_API_KEY) > MASK_KEY_MIN_LENGTH
        else "***"
    )
    print(f"[DEBUG] SETSMART_API_KEY loaded: {masked_key}")
SET_INDEX_SYMBOL = os.getenv("SET_INDEX_SYMBOL", "SET")


def _describe_setsmart_error(exc: httpx.HTTPError, symbol: str, date: str) -> str:
    """Map an httpx failure to the matching SETSMART error message."""
    if isinstance(exc, httpx.TimeoutException):
        return f"SETSMART API timeout after 30s for {symbol} on {date}."
    if isinstance(exc, httpx.HTTPStatusError):
        return f"SETSMART API HTTP error: {exc}"
    return f"Unexpected error fetching SETSMART data: {exc}"


def fetch_setsmart_eod(
    symbol: str,
    date: str,
    transport: httpx.BaseTransport | None = None,
) -> dict | None:
    """Fetch EOD price data from the SETSMART API for a given symbol and date.

    transport: optional httpx transport for injecting a test stub (MockTransport).
    """
    if not SETSMART_API_KEY:
        msg = "SETSMART_API_KEY not set. Skipping market data capture."
        print(f"[SKIP] {msg}")
        log_event("INFO", "capture_market", msg)
        return None

    url = f"{SETSMART_BASE_URL}/api/listed-company-api/eod-price-by-symbol"

    params = {
        "symbol": symbol,
        "startDate": date,
        "endDate": date,
        "adjustedPriceFlag": "N",
    }
    headers = {"api-key": SETSMART_API_KEY, "Accept": "application/json"}

    try:
        with httpx.Client(timeout=30.0, transport=transport) as client:
            response = client.get(url, params=params, headers=headers)
            if response.status_code in [401, 403]:
                msg = f"SETSMART Authentication failed ({response.status_code})."
                print(f"[SKIP] {msg}")
                log_event("ERROR", "capture_market", msg)
                return None
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        msg = _describe_setsmart_error(e, symbol, date)
        log_event("ERROR", "capture_market", msg)
        return None

    if isinstance(data, list) and len(data) > 0:
        log_event(
            "INFO",
            "capture_market",
            f"Successfully fetched data for {symbol}",
            {"date": date},
        )
        return data[0]

    log_event("WARN", "capture_market", f"No EOD data returned for {symbol} on {date}")
    return None


def extract_market_prices(eod: dict) -> tuple[float, float, float]:
    """Extract ATO/ATC/volatility from SETSMART EOD response.

    Expected fields: open, close/high/low or alternate naming.
    Returns (ato_price, atc_price, volatility_index).
    """
    open_price = float(eod.get("open") or eod.get("openPrice") or 0.0)
    close_price = float(eod.get("close") or eod.get("closePrice") or eod.get("last") or 0.0)
    high = float(eod.get("high") or eod.get("highPrice") or close_price)
    low = float(eod.get("low") or eod.get("lowPrice") or open_price)

    # Volatility proxy: (high - low) / mid_price, capped at 0.05
    mid_price = (high + low) / 2
    volatility = round((high - low) / mid_price, 4) if mid_price > 0 else 0.01
    volatility = min(volatility, MAX_INTRADAY_VOLATILITY)

    return open_price, close_price, volatility


# --- I/O Helpers ---


def load_existing(date_str: str, mode: str | None = None) -> dict:
    """Load an existing market data file, or return a minimal skeleton."""
    market_dir = Path(MARKET_DATA_DIR)
    if mode:
        files = sorted(market_dir.glob(f"{date_str}-*-{mode}.json"))
        if files:
            with files[-1].open(encoding="utf-8") as f:
                return json.load(f)

    # Specific preference: when looking for prior ATO (mode is None or ato), prefer *-ato.json
    ato_files = sorted(market_dir.glob(f"{date_str}-*-ato.json"))
    if ato_files:
        with ato_files[-1].open(encoding="utf-8") as f:
            data = json.load(f)
            if data.get("atoPrice") is not None:
                return data

    files = sorted(market_dir.glob(f"{date_str}-*.json"))
    filepath = files[-1] if files else None

    if filepath is None:
        legacy = market_dir / f"{date_str}.json"
        if legacy.exists():
            filepath = legacy

    if filepath and filepath.exists():
        with filepath.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_market_data(record: dict, date_str: str, mode: str) -> str:
    """Write the market data record to market-data/YYYY-MM-DD-HHMMSS-mode.json."""
    market_dir = Path(MARKET_DATA_DIR)
    market_dir.mkdir(exist_ok=True)

    # Use date_str and current ICT time
    now_ict = datetime.now(UTC) + ICT_OFFSET
    time_str = now_ict.strftime("%H%M%S")
    dt = f"{date_str}-{time_str}"

    filepath = market_dir / f"{dt}-{mode}.json"
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    msg = f"Market data written to {filepath}"
    print(f"[SAVE] {msg}")
    log_event("INFO", "capture_market", msg, {"date": date_str, "status": record.get("status")})
    return str(filepath)


# --- Mode Handlers ---


def handle_ato(date_str: str, ato_price: float) -> dict:
    """Create a partial market outcome Observation with ATO price only."""
    log_event("INFO", "capture_market", f"Handling ATO for {date_str}", {"ato_price": ato_price})
    return {
        "@context": "https://schema.org",
        "@type": "Observation",
        "name": f"SET Market Outcome {date_str} (partial — ATO only)",
        "observationDate": date_str,
        "measuredProperty": {
            "@type": "DefinedTerm",
            "name": "Actual Regime",
            "inDefinedTermSet": REGIME_TAXONOMY_URL,
        },
        "variableMeasured": [
            {
                "@type": "QuantitativeValue",
                "name": "ATO Price",
                "value": ato_price,
                "unitText": "SET Index Points",
            },
        ],
        # --- original fields preserved for backward compatibility ---
        "date": date_str,
        "atoPrice": ato_price,
        "status": "partial",
    }


def handle_atc(
    date_str: str,
    atc_price: float,
    volatility_index: float,
    threshold_mean: float = 0.02,
) -> dict:
    """Create or update a complete market outcome Observation.

    Merge with existing ATO data if present.
    """
    existing = load_existing(date_str)
    ato_price: float | None = existing.get("atoPrice")

    if ato_price is None:
        msg = f"No ATO price found for {date_str}. Using ATC as fallback."
        print(f"[WARN] {msg}")
        log_event("WARN", "capture_market", msg)
        ato_price = atc_price  # fallback — zero return

    return_pct = round((atc_price - ato_price) / ato_price * 100, 2) if ato_price > 0 else 0.0
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

    now_ict = datetime.now(UTC) + ICT_OFFSET
    period_start = f"{date_str}T10:00:00+07:00"
    period_end = now_ict.strftime("%Y-%m-%dT%H:%M:%S+07:00")

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
        "variableMeasured": [
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
        ],
        # --- original fields preserved for backward compatibility ---
        "date": date_str,
        "atoPrice": ato_price,
        "atcPrice": atc_price,
        "returnPct": return_pct,
        "volatilityIndex": volatility_index,
        "actualRegime": actual_regime,
        "status": "complete",
    }


# --- Entry Point ---


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for capture modes."""
    parser = argparse.ArgumentParser(description="Capture SET market data (ATO/ATC).")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["ato", "atc"],
        help="Capture mode: ato (open) or atc (close).",
    )
    parser.add_argument(
        "--ato-price",
        type=float,
        help="ATO price (manual, required without --symbol).",
    )
    parser.add_argument(
        "--atc-price",
        type=float,
        help="ATC price (manual, required without --symbol for --mode atc).",
    )
    parser.add_argument(
        "--volatility",
        type=float,
        default=0.01,
        help="Intraday volatility proxy (manual).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.02,
        help="30-day rolling volatility threshold mean.",
    )
    parser.add_argument(
        "--symbol",
        help=(
            "Market symbol (e.g. SET, SET50 or stock ticker). "
            "Fetches live data from API instead of manual prices."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=["setsmart", "finnhub", "yahoo"],
        default="yahoo",
        help="API provider for symbol data (default: yahoo).",
    )
    return parser


def _already_captured(date_str: str, mode: str) -> bool:
    """Return True (and log) if today's market data for this mode already exists."""
    existing = load_existing(date_str, mode=mode)
    if mode == "ato" and existing.get("atoPrice") is not None:
        print(f"[SKIP] ATO data for {date_str} already exists (atoPrice={existing['atoPrice']}).")
        return True
    if mode == "atc" and existing.get("status") == "complete":
        print(f"[SKIP] ATC data for {date_str} already exists (status=complete).")
        return True
    return False


def _fetch_live_prices(
    provider: str,
    symbol: str,
    date_str: str,
    mode: str,
) -> tuple[float, float, float]:
    """Fetch ATO/ATC/volatility from the chosen provider, enforcing fail-closed integrity."""
    if provider == "finnhub":
        log_event(
            "INFO",
            "capture_market",
            f"Starting Finnhub fetch for {symbol}",
            {"mode": mode},
        )
        data = fetch_finnhub_quote(symbol)
        if not data or float(data.get("c", 0.0)) == 0.0:
            error_msg = f"Finnhub API returned no valid quote for {symbol} on {date_str}."
            log_event("ERROR", "capture_market", error_msg)
            raise RuntimeError(error_msg)
        ato_price = float(data.get("o", 0.0))
        atc_price = float(data.get("c", 0.0))
        volatility = 0.01
        print(f"[FINNHUB] ATO={ato_price}, ATC={atc_price}, Vol={volatility}")
        return ato_price, atc_price, volatility

    if provider == "yahoo":
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
        ato_price = float(data.get("o", 0.0))
        atc_price = float(data.get("c", 0.0))
        high_p = float(data.get("h", atc_price))
        low_p = float(data.get("l", ato_price))
        mid_price = (high_p + low_p) / 2
        volatility = round((high_p - low_p) / mid_price, 4) if mid_price > 0 else 0.01
        volatility = min(volatility, MAX_INTRADAY_VOLATILITY)
        print(f"[YAHOO] ATO={ato_price}, ATC={atc_price}, Vol={volatility}")
        return ato_price, atc_price, volatility

    # SETSMART
    log_event(
        "INFO",
        "capture_market",
        f"Starting SETSMART fetch for {symbol}",
        {"mode": mode},
    )
    eod = fetch_setsmart_eod(symbol, date_str)
    if eod is None:
        error_msg = f"SETSMART API returned no data for {symbol} on {date_str}."
        log_event("ERROR", "capture_market", error_msg)
        raise RuntimeError(error_msg)
    ato_price, atc_price, volatility = extract_market_prices(eod)
    print(f"[SETSMART] ATO={ato_price}, ATC={atc_price}, Vol={volatility}")
    return ato_price, atc_price, volatility


def main() -> None:
    """Capture ATO or ATC market data for today and persist the Observation."""
    parser = _build_parser()
    args = parser.parse_args()
    date_str = (datetime.now(UTC) + ICT_OFFSET).strftime("%Y-%m-%d")

    # Idempotent: skip if today already has market data for this mode
    if _already_captured(date_str, args.mode):
        return

    try:
        if args.mode == "ato":
            if args.symbol:
                ato_price, _, _ = _fetch_live_prices(args.provider, args.symbol, date_str, "ato")
            else:
                if args.ato_price is None:
                    parser.error("--ato-price is required for --mode ato (or use --symbol).")
                log_event("INFO", "capture_market", "Starting manual price entry", {"mode": "ato"})
                ato_price = args.ato_price
            record = handle_ato(date_str, ato_price)
        else:
            if args.symbol:
                _, atc_price, volatility = _fetch_live_prices(
                    args.provider,
                    args.symbol,
                    date_str,
                    "atc",
                )
            else:
                if args.atc_price is None:
                    parser.error("--atc-price is required for --mode atc (or use --symbol).")
                log_event("INFO", "capture_market", "Starting manual price entry", {"mode": "atc"})
                atc_price = args.atc_price
                volatility = args.volatility
            record = handle_atc(date_str, atc_price, volatility, args.threshold)

        save_market_data(record, date_str, args.mode)
        print(f"[DONE] Market {args.mode.upper()} capture complete.")
    except Exception as e:
        error_msg = f"Market capture failed: {e}"
        log_failure("capture_market", error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
