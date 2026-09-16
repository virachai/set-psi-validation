"""Validate intraday workflow schedule and step-decider invariants."""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(".github/workflows/intraday-pipeline.yml")

EXPECTED_CRONS = {
    "3,13,23,33,43,53 1 * * 1-5",
    "3,13,23,33,43,53 2 * * 1-5",
    "3,13,23,33,43,53 3-4 * * 1-5",
    "3,13,23,33,43,53 5 * * 1-5",
    "3,13,23,33,43,53 6 * * 1-5",
    "33,43,53 7 * * 1-5",
    "3,13,23,33,43,53 8 * * 1-5",
    "3,13,23 9 * * 1-5",
    "48 9 * * 1-5",
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
        "prediction-am": "predictions_loader.py --session am",
        "prediction-full-day": "predictions_loader.py --session full_day",
        "prediction-pm": "predictions_loader.py --session pm",
        "ato": "capture_market.py --mode ato",
        "noon": "capture_market.py --mode noon",
        "pmopen": "capture_market.py --mode pmopen",
        "atc": "capture_market.py --mode atc",
        "validation": "validation_engine.py",
    }
    for step, command in required_steps.items():
        if step not in text or command not in text:
            message = f"Workflow step '{step}' is missing expected command '{command}'"
            raise SystemExit(message)

    required_boundaries = [
        'H_ICT" -lt 8',
        'H_ICT" -ge 17',
        'H_ICT" -eq 16 && "$M_ICT" -ge 40',
        'H_ICT" -eq 16 && "$M_ICT" -ge 20',
        'H_ICT" -ge 13',
        'H_ICT" -eq 12 && "$M_ICT" -ge 30',
        'H_ICT" -ge 10',
        'H_ICT" -ge 9',
        'H_ICT" -ge 8',
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
