# /// script
# dependencies = ["python-dotenv", "httpx"]
# ///
"""
Market Data Capture (ATO / ATC)

Captures SET market open (ATO) and close (ATC) data, computes intraday metrics,
derives the actual regime, and saves as a schema.org-compliant Observation JSON-LD file.

Modes:
  --mode ato   : Capture opening price (partial record, awaits ATC).
  --mode atc   : Capture closing price, compute return/volatility, derive regime.

Output: market-data/YYYY-MM-DD.json

Governance: Compliant with "Lean PSI Validator" principles.
"""

import os
import json
import sys
import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# --- Constants ---

ICT_OFFSET = timedelta(hours=7)
MARKET_DATA_DIR = "market-data"
REGIME_TAXONOMY_URL = (
    "https://raw.githubusercontent.com/virachai/set-psi-validation"
    "/main/docs/regime-taxonomy.jsonld"
)

VALID_REGIMES = ["Bullish", "Bearish", "Sideways", "Risk-Off", "Crisis"]

# --- SETSMART API ---

SETSMART_BASE_URL = "https://www.setsmart.com"
SETSMART_API_KEY = os.getenv("SETSMART_API_KEY")
SET_INDEX_SYMBOL = os.getenv("SET_INDEX_SYMBOL", "SET")


def fetch_setsmart_eod(symbol: str, date: str) -> dict:
    """Fetch EOD price data from SETSMART API for a given symbol and date."""
    if not SETSMART_API_KEY:
        raise EnvironmentError("SETSMART_API_KEY not set.")

    url = f"{SETSMART_BASE_URL}/api/listed-company-api/eod-price-by-symbol"
    params = {
        "symbol": symbol,
        "startDate": date,
        "endDate": date,
        "adjustedPriceFlag": "N",
    }
    headers = {"api-key": SETSMART_API_KEY, "Accept": "application/json"}

    import httpx

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    if isinstance(data, list) and len(data) > 0:
        return data[0]
    raise ValueError(f"No EOD data for {symbol} on {date}")


def extract_market_prices(eod: dict) -> tuple[float, float, float]:
    """Extract ATO/ATC/volatility from SETSMART EOD response.

    Expected fields: open, close/high/low or alternate naming.
    Returns (ato_price, atc_price, volatility_index).
    """
    open_price = eod.get("open") or eod.get("openPrice") or 0.0
    close_price = eod.get("close") or eod.get("closePrice") or eod.get("last") or 0.0
    high = eod.get("high") or eod.get("highPrice") or close_price
    low = eod.get("low") or eod.get("lowPrice") or open_price

    # Volatility proxy: (high - low) / open, capped at 0.05
    volatility = round((high - low) / open_price, 4) if open_price else 0.01
    volatility = min(volatility, 0.05)

    return float(open_price), float(close_price), volatility


# --- Regime Derivation Logic (mirrors validation_engine.py) ---


def derive_actual_regime(
    ato_price: float,
    atc_price: float,
    volatility_index: float,
    threshold_mean: float,
) -> str:
    """
    Derives the actual market regime based on intraday return and volatility.
    Logic defined in docs/research_reports/001-actual-regime-derivation-logic-v01.md.
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
        return "Sideways"
    else:
        return "Unclassified"


# --- I/O Helpers ---


def load_existing(date_str: str) -> dict:
    """Loads an existing market data file, or returns a minimal skeleton."""
    filepath = os.path.join(MARKET_DATA_DIR, f"{date_str}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_market_data(record: dict, date_str: str) -> str:
    """Writes the market data record to market-data/YYYY-MM-DD.json."""
    os.makedirs(MARKET_DATA_DIR, exist_ok=True)
    filepath = os.path.join(MARKET_DATA_DIR, f"{date_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[SAVE] Market data written to {filepath}")
    return filepath


# --- Mode Handlers ---


def handle_ato(date_str: str, ato_price: float) -> dict:
    """Creates a partial market outcome Observation with ATO price only."""
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
    """
    Creates/updates a complete market outcome Observation.
    Merges with existing ATO data if present.
    """
    existing = load_existing(date_str)
    ato_price: Optional[float] = existing.get("atoPrice")

    if ato_price is None:
        print("[WARN] No ATO price found for this date. Using ATC as fallback.")
        ato_price = atc_price  # fallback — zero return

    return_pct = round((atc_price - ato_price) / ato_price * 100, 2)
    actual_regime = derive_actual_regime(ato_price, atc_price, volatility_index, threshold_mean)

    now_ict = datetime.now(timezone.utc) + ICT_OFFSET
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture SET market data (ATO/ATC).")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["ato", "atc"],
        help="Capture mode: ato (open) or atc (close).",
    )
    parser.add_argument(
        "--ato-price", type=float, help="ATO price (manual, required without --symbol)."
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
        help="SETSMART symbol (e.g. SET, SET50). Fetches live data from API instead of manual prices.",
    )
    args = parser.parse_args()

    now_ict = datetime.now(timezone.utc) + ICT_OFFSET
    date_str = now_ict.strftime("%Y-%m-%d")

    try:
        if args.symbol:
            print(f"[SETSMART] Fetching EOD data for {args.symbol} on {date_str}...")
            eod = fetch_setsmart_eod(args.symbol, date_str)
            ato_price, atc_price, volatility = extract_market_prices(eod)
            print(f"[SETSMART] ATO={ato_price}, ATC={atc_price}, Vol={volatility}")

            if args.mode == "ato":
                record = handle_ato(date_str, ato_price)
            else:
                record = handle_atc(date_str, atc_price, volatility, args.threshold)
        else:
            # Manual mode
            if args.mode == "ato":
                if args.ato_price is None:
                    parser.error("--ato-price is required for --mode ato (or use --symbol).")
                record = handle_ato(date_str, args.ato_price)
            else:
                if args.atc_price is None:
                    parser.error("--atc-price is required for --mode atc (or use --symbol).")
                record = handle_atc(date_str, args.atc_price, args.volatility, args.threshold)

        save_market_data(record, date_str)
        print(f"[DONE] Market {args.mode.upper()} capture complete.")
    except Exception as e:
        print(f"[ERROR] Market capture failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
