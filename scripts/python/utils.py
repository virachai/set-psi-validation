import os
import json
from datetime import datetime, timezone

LOG_DIR = "logs"
FAILURE_LOG = os.path.join(LOG_DIR, "failures.jsonl")


def log_failure(component: str, error_msg: str):
    """Logs a critical failure to failures.jsonl for observability."""
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "error": error_msg,
    }
    with open(FAILURE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[ALERT] Failure logged in {component}: {error_msg}")
