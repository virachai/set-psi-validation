"""Validate intraday workflow schedule and step-decider invariants."""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/intraday-pipeline.yml")

# Single daily cycle (RFC 020): a morning prediction retry window and a
# post-close ATC capture + validation retry window.
EXPECTED_CRONS = {
    "0,30 22,23 * * 0-4",  # ICT 05:00-06:59 Mon-Fri — prediction
    "0,30 0,1,2 * * 1-5",  # ICT 07:00-09:59 — prediction
    "45,15 9,10,11,12,13,14,15,16 * * 1-5",  # ICT 16:45-23:59 — atc + validation
}


def _workflow_text() -> str:
    if not WORKFLOW.is_file():
        raise SystemExit(f"Missing workflow: {WORKFLOW}")  # noqa: TRY003, EM102
    return WORKFLOW.read_text(encoding="utf-8")


def validate() -> None:
    """Validate cron schedules and step-decider guards in the intraday workflow."""
    text = _workflow_text()
    crons = set(re.findall(r'cron:\s*"([^"]+)"', text))
    missing = EXPECTED_CRONS - crons
    unexpected = crons - EXPECTED_CRONS
    if missing or unexpected:
        message = f"Cron mismatch; missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        raise SystemExit(message)

    required_steps = {
        "prediction-full-day": "predictions_loader.py --session full_day",
        "atc-and-validate": "capture_market.py --mode atc",
        "validation": "validation_engine.py",
    }
    for step, command in required_steps.items():
        if step not in text or command not in text:
            message = f"Workflow step '{step}' is missing expected command '{command}'"
            raise SystemExit(message)

    required_boundaries = [
        'H_ICT" -ge 5 && "$H_ICT" -lt 10',
        'H_ICT" -eq 16 && "$M_ICT" -ge 45',
        'H_ICT" -ge 17 && "$H_ICT" -le 23',
    ]
    for boundary in required_boundaries:
        if boundary not in text:
            message = f"Missing step-decider boundary: {boundary}"
            raise SystemExit(message)

    print(
        f"[OK] Workflow validated: {len(crons)} cron schedules, "
        f"{len(required_steps)} pipeline steps.",
    )


if __name__ == "__main__":
    validate()
