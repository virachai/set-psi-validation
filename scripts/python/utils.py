"""Shared JSONL logging utilities for the PSI validation pipeline scripts."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOG_DIR = Path("logs")
FAILURE_LOG = LOG_DIR / "failures.jsonl"
APP_LOG = LOG_DIR / "app.jsonl"


def log_event(
    level: str,
    module: str,
    message: str,
    context: dict[str, Any] | None = None,
    log_file: Path = APP_LOG,
) -> None:
    """Log a structured event to a JSONL file."""
    LOG_DIR.mkdir(exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level.upper(),
        "module": module,
        "message": message,
    }
    if context:
        # Filter out sensitive keys from context if any
        safe_context = {
            k: (v if "key" not in k.lower() and "token" not in k.lower() else "***")
            for k, v in context.items()
        }
        entry["context"] = safe_context

    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    if level.upper() in ["ERROR", "CRITICAL"]:
        print(f"[{level.upper()}] {module}: {message}")


def log_failure(component: str, error_msg: str) -> None:
    """Log a critical failure to failures.jsonl for observability.

    Maintained for backward compatibility.
    """
    log_event("ERROR", component, error_msg, log_file=FAILURE_LOG)
    # Also log to app log for continuity
    log_event("ERROR", component, error_msg)


def log_warning(component: str, warn_msg: str) -> None:
    """Log a warning event to the app log."""
    log_event("WARNING", component, warn_msg)
