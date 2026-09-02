"""JSON-LD Enricher.

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

import argparse
import json
import sys
from pathlib import Path

# --- Directory-to-Type Mapping ---

DIRECTORY_MAP: dict[str, dict[str, str]] = {
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


def enrich_file(
    filepath: str,
    schema_meta: dict[str, str],
    *,
    validate_only: bool = False,
) -> bool:
    """Read a JSON file and inject @context/@type if missing.

    Returns True if the file is valid/enriched, False on error.
    """
    try:
        with Path(filepath).open(encoding="utf-8") as f:
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

    with Path(filepath).open("w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"[ENRICH] {filepath} — added @context/@type")
    return True


def process_directory(directory: str, *, validate_only: bool = False) -> int:
    """Process all .json files in a directory.

    Returns the count of files that failed.
    """
    path = Path(directory)
    if not path.is_dir():
        print(f"[SKIP] Directory not found: {directory}")
        return 0

    dirname = path.name
    schema_meta = DIRECTORY_MAP.get(dirname, {})
    if not schema_meta:
        print(f"[SKIP] No schema mapping for directory '{directory}'")
        return 0

    failures = 0
    for entry in sorted(path.iterdir()):
        if entry.suffix != ".json":
            continue
        if not enrich_file(str(entry), schema_meta, validate_only=validate_only):
            failures += 1

    return failures


# --- Entry Point ---


def main() -> None:
    """Enrich or validate schema.org metadata across all output directories."""
    parser = argparse.ArgumentParser(
        description="Enrich JSON files with schema.org @context/@type.",
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
        failures = process_directory(directory, validate_only=args.validate_only)
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
