import os
import json
from datetime import datetime, timezone
from typing import Any, Optional

LOG_DIR = "logs"
FAILURE_LOG = os.path.join(LOG_DIR, "failures.jsonl")
APP_LOG = os.path.join(LOG_DIR, "app.jsonl")


def log_event(
    level: str,
    module: str,
    message: str,
    context: Optional[dict[str, Any]] = None,
    log_file: str = APP_LOG,
):
    """Logs a structured event to a JSONL file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
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

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    if level.upper() in ["ERROR", "CRITICAL"]:
        print(f"[{level.upper()}] {module}: {message}")


def log_failure(component: str, error_msg: str):
    """Logs a critical failure to failures.jsonl for observability.
    Maintained for backward compatibility.
    """
    log_event("ERROR", component, error_msg, log_file=FAILURE_LOG)
    # Also log to app log for continuity
    log_event("ERROR", component, error_msg)


def log_warning(component: str, warn_msg: str):
    """Logs a warning event to the app log."""
    log_event("WARNING", component, warn_msg)
