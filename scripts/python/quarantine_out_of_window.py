#!/usr/bin/env python3
"""Quarantine PSI artifacts that were produced outside the window they claim.

Three checks, all driven by the windows the pipeline already declares:

1. market-data captures whose filename time falls outside `CAPTURE_WINDOWS[mode]`
   — they recorded the wrong price under that snapshot's label.
2. predictions whose `observationDate` falls outside `MARKET_WINDOWS[session]`
   — a forecast made before its window opened was not made on the information
   the hypothesis is supposed to be tested against.
3. validation records derived from either of the above.

Offenders move to `<dir>/quarantine/` rather than being deleted, so the audit
trail survives. The workflow's commit step globs `-maxdepth 1`, so quarantined
files drop out of the pipeline automatically.

Usage:
    uv run scripts/python/quarantine_out_of_window.py [--apply]

Without --apply it only reports what it would move.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from capture_market import CAPTURE_WINDOWS
from predictions_loader import MARKET_WINDOWS, _to_ict

MARKET_DATA_DIR = Path("market-data")
PREDICTIONS_DIR = Path("predictions")
VALIDATION_DIR = Path("validation")

FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{6})-(\w+)\.json$")

# Which market-data captures each prediction session's actual regime depends on.
# Mirrors validation_engine._resolve_market_outcome, including the *inputs* to the
# derived returns: the atc record's returnPct is computed against the stored ATO
# price and its afternoonReturnPct against the stored PM-open price, so a bad ato
# or pmopen capture poisons the atc-scored sessions too.
SESSION_SOURCE_MODES = {
    "am": {"ato", "noon"},
    "pm": {"pmopen", "atc"},
    "full_day": {"ato", "atc"},
}


def find_out_of_window() -> list[tuple[Path, str]]:
    """Return (path, reason) for every market-data file captured outside its window."""
    offenders = []
    for path in sorted(MARKET_DATA_DIR.glob("*.json")):
        match = FILENAME_RE.match(path.name)
        if not match:
            continue
        _, hhmmss, mode = match.groups()
        window = CAPTURE_WINDOWS.get(mode)
        if window is None:
            continue
        open_time, cutoff = window
        captured = datetime.strptime(hhmmss, "%H%M%S").time()  # noqa: DTZ007 — wall clock only
        if captured < open_time:
            offenders.append((path, f"{captured} is before the {mode} window opens ({open_time})"))
        elif cutoff is not None and captured >= cutoff:
            offenders.append((path, f"{captured} is at/after the {mode} cutoff ({cutoff})"))
    return offenders


def find_out_of_window_predictions() -> list[tuple[Path, str]]:
    """Return (path, reason) for predictions timestamped outside their session window."""
    offenders = []
    for path in sorted(PREDICTIONS_DIR.glob("*.json")):
        match = FILENAME_RE.match(path.name)
        if not match:
            continue
        _, _, session = match.groups()
        window = MARKET_WINDOWS.get(session)
        if not window:
            continue
        observed = json.loads(path.read_text(encoding="utf-8")).get("observationDate")
        if not observed:
            continue
        made_at = _to_ict(datetime.fromisoformat(observed)).strftime("%H:%M:%S")
        if made_at < window["open"]:
            offenders.append(
                (
                    path,
                    f"made at {made_at} ICT, before the {session} window opens ({window['open']})",
                ),
            )
        elif made_at > window["cutoff"]:
            offenders.append(
                (path, f"made at {made_at} ICT, after the {session} cutoff ({window['cutoff']})"),
            )
    return offenders


def dependent_validations(bad_dates_by_mode: dict[str, set[str]]) -> list[tuple[Path, str]]:
    """Return validation records whose actual-regime source was quarantined."""
    dependents = []
    for path in sorted(VALIDATION_DIR.glob("*.json")):
        match = FILENAME_RE.match(path.name)
        if not match:
            continue
        date_str, _, session = match.groups()
        tainted = sorted(
            mode
            for mode in SESSION_SOURCE_MODES.get(session, set())
            if date_str in bad_dates_by_mode.get(mode, set())
        )
        if tainted:
            dependents.append((path, f"derived from quarantined {', '.join(tainted)} capture(s)"))
    return dependents


def main() -> None:
    """Report, and with --apply move, every out-of-window artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="actually move the files")
    args = parser.parse_args()

    offenders = find_out_of_window()
    bad_dates_by_mode: dict[str, set[str]] = {}
    for path, _ in offenders:
        date_str, _, mode = FILENAME_RE.match(path.name).groups()  # type: ignore[union-attr]
        bad_dates_by_mode.setdefault(mode, set()).add(date_str)

    bad_predictions = find_out_of_window_predictions()
    bad_sessions = {FILENAME_RE.match(p.name).groups()[2] for p, _ in bad_predictions}  # type: ignore[union-attr]

    targets = offenders + bad_predictions + dependent_validations(bad_dates_by_mode)
    # A validation record for a quarantined prediction has nothing left to score.
    targets += [
        (path, "scores a quarantined prediction")
        for path in sorted(VALIDATION_DIR.glob("*.json"))
        if (m := FILENAME_RE.match(path.name)) and m.groups()[2] in bad_sessions
    ]
    if not targets:
        print("[OK] No out-of-window artifacts found.")
        return

    seen: set[Path] = set()
    for path, reason in targets:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        print(f"[{'MOVE' if args.apply else 'DRY-RUN'}] {path} — {reason}")
        if args.apply:
            dest = path.parent / "quarantine" / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            path.replace(dest)

    verb = "quarantined" if args.apply else "would be quarantined"
    print(f"\n{len(seen)} artifact(s) {verb}.")
    if not args.apply:
        print("Re-run with --apply to move them.")


if __name__ == "__main__":
    main()
