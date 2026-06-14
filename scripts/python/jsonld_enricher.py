# /// script
# dependencies = []
# ///
"""
JSON-LD Enricher

Post-processing step that reads existing JSON files in predictions/, market-data/,
validation/, and reports/ directories, then injects or validates schema.org
@context and @type metadata.

This ensures all output artifacts conform to the schema.org mapping defined in
docs/research_reports/008-schema-org-mapping-v01.md.

Usage:
  uv run scripts/python/jsonld_enricher.py
  uv run scripts/python/jsonld_enricher.py --validate-only

Governance: Compliant with "Lean PSI Validator" principles.
"""

import os
import json
import sys
import argparse
from typing import Dict, Optional

# --- Directory-to-Type Mapping ---

DIRECTORY_MAP: Dict[str, dict] = {
    "predictions": {
        "@context": "https://schema.org",
        "@type": "Observation",
    },
    "market-data": {
        "@context": "https://schema.org",
        "@type": "Observation",
    },
    "validation": {
        "@context": "https://schema.org",
        "@type": "Observation",
    },
    "reports": {
        "@context": "https://schema.org",
        "@type": "Dataset",
    },
}

REQUIRED_CONTEXT = "https://schema.org"


def enrich_file(filepath: str, schema_meta: dict, validate_only: bool = False) -> bool:
    """
    Reads a JSON file and injects @context/@type if missing.
    Returns True if the file is valid/enriched, False on error.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[FAIL] {filepath} — {e}")
        return False

    if not isinstance(data, dict):
        print(f"[SKIP] {filepath} — not a JSON object (skipped)")
        return True

    has_context = data.get("@context") == REQUIRED_CONTEXT
    has_type = "@type" in data

    if has_context and has_type:
        print(f"[PASS] {filepath} — already enriched")
        return True

    if validate_only:
        missing = []
        if not has_context:
            missing.append("@context")
        if not has_type:
            missing.append("@type")
        print(f"[FAIL] {filepath} — missing {', '.join(missing)}")
        return False

    # Inject schema.org metadata at the top (preserve field order)
    enriched = {}
    enriched["@context"] = schema_meta["@context"]
    enriched["@type"] = schema_meta["@type"]
    enriched.update(data)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"[ENRICH] {filepath} — added @context/@type")
    return True


def process_directory(directory: str, validate_only: bool = False) -> int:
    """
    Processes all .json files in a directory.
    Returns count of files that failed.
    """
    if not os.path.isdir(directory):
        print(f"[SKIP] Directory not found: {directory}")
        return 0

    schema_meta = DIRECTORY_MAP.get(directory, {})
    if not schema_meta:
        print(f"[SKIP] No schema mapping for directory '{directory}'")
        return 0

    failures = 0
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(directory, filename)
        if not enrich_file(filepath, schema_meta, validate_only):
            failures += 1

    return failures


# --- Entry Point ---


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich JSON files with schema.org @context/@type."
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing enrichment, do not modify files.",
    )
    parser.add_argument(
        "--dirs",
        nargs="*",
        default=list(DIRECTORY_MAP.keys()),
        help="Directories to process (default: all mapped directories).",
    )
    args = parser.parse_args()

    total_failures = 0
    for directory in args.dirs:
        failures = process_directory(directory, args.validate_only)
        total_failures += failures

    action = "Validation" if args.validate_only else "Enrichment"
    if total_failures == 0:
        print(f"\n[SUCCESS] {action} complete — all files OK.")
    else:
        print(f"\n[WARN] {action} complete — {total_failures} file(s) had errors.")
        if args.validate_only:
            sys.exit(1)


if __name__ == "__main__":
    main()
