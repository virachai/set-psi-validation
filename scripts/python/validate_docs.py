# /// script
# dependencies = []
# ///
import os
import re
from typing import List


def validate_naming(path: str) -> bool:
    """
    Validates that all files in the given directory (except README.md)
    follow the NNN-kebab-case-vNN.ext pattern.
    """
    if not os.path.exists(path):
        print(f"[SKIP] Directory not found: {path}")
        return True

    # Pattern: NNN-kebab-case-vNN.ext
    # Adjusted to support various extensions (md, json)
    pattern = re.compile(r"^\d{3}-[a-z0-9-]+-v\d{2}\.(md|json)$")
    all_pass = True

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.upper() in ["README.MD", "FLOW.MD", "ROADMAP.MD"]:
                continue
            if not pattern.match(file):
                print(f"[FAIL] Invalid naming: {file} in {root}")
                all_pass = False
            else:
                print(f"[PASS] Valid naming: {file}")

    return all_pass


if __name__ == "__main__":
    # Validate documentation directories
    targets: List[str] = ["docs/research_reports", "docs"]
    results = [validate_naming(t) for t in targets]

    if all(results):
        print("\n[SUCCESS] All documentation naming standards met.")
    else:
        print("\n[ERROR] Documentation naming violations found.")
        exit(1)
