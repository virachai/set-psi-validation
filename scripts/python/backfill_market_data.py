# /// script
# dependencies = ["python-dotenv", "httpx", "yfinance", "pandas"]
# ///
"""Rebuild market-data captures for past dates from Yahoo 30-minute intraday bars.

Live capture reads a *current* quote, so a run that fires outside its window
records the wrong price (see `CAPTURE_WINDOWS` in capture_market.py). Historical
30m bars carry their own ICT timestamps, so each checkpoint can be recovered at
the exact window it belongs to:

    ato     open  of the 10:00 bar   (SET morning session open)
    noon    close of the 12:30 bar   (morning session close / lunch break)
    pmopen  open  of the 14:30 bar   (SET afternoon session open)
    atc     the existing atc record's atcPrice, else the last 30m bar's close

ATC is NOT re-derived from bars. The final 30m bar ends at 16:30 and so excludes
the closing auction, which is precisely the print "ATC" names, and Yahoo returns
no historical daily series for ^SET.BK. The atc captures already on disk were
taken after 16:30 by the live path, so their atcPrice is genuine — the backfill
keeps it and only recomputes the returns that were derived from bad ATO/PM-open
inputs. A date with no atc record falls back to the last intraday close, which
understates the auction.

Records are built with the same `handle_*` functions the live path uses, so the
schema and regime derivation stay single-sourced. Each file is written under the
window's true ICT time, so `quarantine_out_of_window.py` passes it.

Yahoo retains 30m bars for roughly the last 60 days; older dates cannot be
recovered this way.

Usage:
    uv run scripts/python/backfill_market_data.py --start 2026-09-08 --end 2026-09-15 [--apply]
"""

import argparse
import json
import sys
from datetime import date, time, timedelta
from pathlib import Path

import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent))

from capture_market import (
    MAX_INTRADAY_VOLATILITY,
    compute_rolling_threshold_mean,
    handle_atc,
    handle_ato,
    handle_noon,
    handle_pmopen,
    save_market_data,
)

DEFAULT_SYMBOL = "^SET.BK"
BAR_SOURCE = "yahoo-30m"

ATO_BAR = time(10, 0)
NOON_BAR = time(12, 30)
PMOPEN_BAR = time(14, 30)
ATC_STAMP = time(16, 45)  # after the 16:30 closing auction settles

# Bars belonging to the morning session (ATO -> lunch break), used for the
# morning volatility proxy.
MORNING_END = time(12, 30)


def _volatility(high: float, low: float) -> float:
    """Volatility proxy: (high - low) / mid, capped — mirrors extract_market_prices."""
    mid = (high + low) / 2
    vol = round((high - low) / mid, 4) if mid > 0 else 0.01
    return min(vol, MAX_INTRADAY_VOLATILITY)


def _bar_at(day_bars, at: time):  # noqa: ANN001, ANN202 — pandas DataFrame
    """Return the bar stamped exactly `at`, or None when the session lacks it."""
    matches = day_bars[[t.time() == at for t in day_bars.index]]
    return None if matches.empty else matches.iloc[0]


def _stamp_provenance(record: dict, source: str) -> dict:
    """Mark a record as reconstructed, not captured live.

    A backfilled file is written with a synthetic filename time (the window it
    represents, not the moment it was written), so without this stamp it is
    byte-indistinguishable from a live capture. `capture_market._mark_bypass`
    plays the same role for an out-of-window live capture.
    """
    record["backfilledFrom"] = source
    return record


def _supersede(date_str: str, mode: str, keep: Path) -> None:
    """Drop earlier captures of the same date+mode that this backfill replaces.

    Every resolver in the pipeline picks `sorted(glob(...))[-1]`, so leaving the
    old record in place would silently win whenever its wall-clock stamp sorts
    later than the backfilled one. Superseded files go to the quarantine tree
    rather than being deleted, keeping the audit trail.
    """
    for path in sorted(Path("market-data").glob(f"{date_str}-*-{mode}.json")):
        if path == keep:
            continue
        dest = Path("market-data") / "quarantine" / "superseded" / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        path.replace(dest)
        print(f"[SUPERSEDE] {path.name} -> {dest.parent}")


def _existing_atc(date_str: str) -> tuple[float, float] | None:
    """Return (atcPrice, volatilityIndex) from the date's already-captured atc record."""
    files = sorted(Path("market-data").glob(f"{date_str}-*-atc.json"))
    if not files:
        return None
    data = json.loads(files[-1].read_text(encoding="utf-8"))
    price, vol = data.get("atcPrice"), data.get("volatilityIndex")
    return None if price is None or vol is None else (float(price), float(vol))


def backfill_day(day_bars, date_str: str, *, apply: bool) -> None:  # noqa: ANN001
    """Rebuild all four checkpoints for one trading date, in dependency order."""
    ato_bar = _bar_at(day_bars, ATO_BAR)
    noon_bar = _bar_at(day_bars, NOON_BAR)
    pmopen_bar = _bar_at(day_bars, PMOPEN_BAR)
    if ato_bar is None or noon_bar is None or pmopen_bar is None:
        print(f"[SKIP] {date_str}: incomplete intraday session in Yahoo bars.")
        return

    morning = day_bars[[t.time() <= MORNING_END for t in day_bars.index]]
    ato_price = float(ato_bar["Open"])
    noon_price = float(noon_bar["Close"])
    pm_open_price = float(pmopen_bar["Open"])
    morning_vol = _volatility(float(morning["High"].max()), float(morning["Low"].min()))
    captured_atc = _existing_atc(date_str)
    if captured_atc is not None:
        atc_price, day_vol = captured_atc
    else:
        atc_price = float(day_bars.iloc[-1]["Close"])
        day_vol = _volatility(float(day_bars["High"].max()), float(day_bars["Low"].min()))
        print(f"[WARN] {date_str}: no captured atc record — using the 16:00 bar close.")

    print(
        f"[{'WRITE' if apply else 'DRY-RUN'}] {date_str}: "
        f"ato={ato_price:.2f} noon={noon_price:.2f} "
        f"pmopen={pm_open_price:.2f} atc={atc_price:.2f} vol={day_vol}",
    )
    if not apply:
        return

    # Order matters: handle_noon reads the ato record, handle_atc reads both.
    # Each record supersedes its predecessor before the next handler reads it.
    written = save_market_data(
        _stamp_provenance(handle_ato(date_str, ato_price), BAR_SOURCE),
        date_str,
        "ato",
        ATO_BAR,
    )
    _supersede(date_str, "ato", Path(written))

    threshold = compute_rolling_threshold_mean(date_str)
    written = save_market_data(
        _stamp_provenance(handle_noon(date_str, noon_price, morning_vol, threshold), BAR_SOURCE),
        date_str,
        "noon",
        NOON_BAR,
    )
    _supersede(date_str, "noon", Path(written))

    written = save_market_data(
        _stamp_provenance(handle_pmopen(date_str, pm_open_price), BAR_SOURCE),
        date_str,
        "pmopen",
        PMOPEN_BAR,
    )
    _supersede(date_str, "pmopen", Path(written))

    written = save_market_data(
        _stamp_provenance(
            handle_atc(date_str, atc_price, day_vol, threshold),
            f"{BAR_SOURCE}+captured-atc",
        ),
        date_str,
        "atc",
        ATC_STAMP,
    )
    _supersede(date_str, "atc", Path(written))


def main() -> None:
    """Fetch intraday bars for the requested range and rebuild each trading day."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="First date to rebuild (YYYY-MM-DD).")
    parser.add_argument("--end", required=True, help="Last date to rebuild, inclusive.")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--apply", action="store_true", help="Actually write the records.")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    end_exclusive = (end + timedelta(days=1)).isoformat()
    bars = yf.Ticker(args.symbol).history(
        start=start.isoformat(),
        end=end_exclusive,
        interval="30m",
    )
    if bars.empty:
        print(f"[ERROR] No intraday bars returned for {args.symbol} in {start}..{end}.")
        sys.exit(1)

    for day in sorted({t.date() for t in bars.index}):
        if not start <= day <= end:
            continue
        day_bars = bars[[t.date() == day for t in bars.index]]
        backfill_day(day_bars, day.isoformat(), apply=args.apply)

    if not args.apply:
        print("\nRe-run with --apply to write these records.")


if __name__ == "__main__":
    main()
