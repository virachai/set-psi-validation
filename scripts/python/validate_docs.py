"""Validate that documentation files follow the NNN-kebab-case-vNN naming standard."""

import os
import re
import sys
from pathlib import Path

EXEMPT_FILENAMES = {"README.MD", "FLOW.MD", "ROADMAP.MD"}


def validate_naming(path: str) -> bool:
    """Validate that all files in the given directory follow the standard.

    Every file except README.md / FLOW.md / ROADMAP.md must match the
    NNN-kebab-case-vNN pattern with a .md or .json extension.
    """
    if not Path(path).exists():
        print(f"[SKIP] Directory not found: {path}")
        return True

    pattern = re.compile(r"^\d{3}-[a-z0-9-]+-v\d{2}\.(md|json)$")
    all_pass = True

    for root, _, files in os.walk(path):
        for file in files:
            if file.upper() in EXEMPT_FILENAMES:
                continue
            if not pattern.match(file):
                print(f"[FAIL] Invalid naming: {file} in {root}")
                all_pass = False
            else:
                print(f"[PASS] Valid naming: {file}")

    return all_pass


if __name__ == "__main__":
    # Validate documentation directories
    targets: list[str] = ["docs/research_reports", "docs"]
    results = [validate_naming(t) for t in targets]

    if all(results):
        print("\n[SUCCESS] All documentation naming standards met.")
    else:
        print("\n[ERROR] Documentation naming violations found.")
        sys.exit(1)
