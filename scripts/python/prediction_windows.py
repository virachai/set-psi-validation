"""Authoritative ICT prediction-session windows and timestamp helpers."""

import os
from datetime import datetime, time, timedelta, timezone

ICT_OFFSET = timedelta(hours=7)
ICT = timezone(ICT_OFFSET)

MARKET_WINDOWS: dict[str, dict[str, str]] = {
    "full_day": {
        "open": os.getenv("PSI_OPEN_FULL_DAY", "09:00:00"),
        "cutoff": os.getenv("PSI_CUTOFF_FULL_DAY", "10:00:00"),
    },
}


def _window_times(session: str) -> tuple[time, time]:
    window = MARKET_WINDOWS[session]
    return time.fromisoformat(window["open"]), time.fromisoformat(window["cutoff"])


def validate_prediction_timestamp(
    timestamp_iso: str,
    session: str,
    expected_date: str | None = None,
) -> tuple[bool, str | None]:
    """Return whether a prediction timestamp is inside its authoritative window."""
    reason: str | None = None
    dt = None
    try:
        dt = datetime.fromisoformat(timestamp_iso)
    except ValueError:
        reason = f"Invalid timestamp '{timestamp_iso}'."
    if reason is None and dt is not None and dt.tzinfo is None:
        reason = f"Timestamp '{timestamp_iso}' has no timezone offset."
    if reason is None and session not in MARKET_WINDOWS:
        reason = f"Unknown prediction session '{session}'."

    if reason is None and dt is not None:
        dt_ict = dt.astimezone(ICT)
        if expected_date is not None and dt_ict.date().isoformat() != expected_date:
            reason = (
                f"Timestamp date {dt_ict.date().isoformat()} does not match "
                f"expected trading date {expected_date} for {session} session."
            )
        else:
            open_time, cutoff = _window_times(session)
            if dt_ict.time() < open_time:
                reason = f"Timestamp is before the {session} window opens ({open_time})."
            elif dt_ict.time() > cutoff:
                reason = f"Timestamp is after the {session} cutoff ({cutoff})."
    return reason is None, reason
