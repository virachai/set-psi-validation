# Taxonomy Renamed & CI Green

## Metadata

- **Date:** 2026-06-14
- **Author:** Gemini CLI
- **Status:** COMPLETED

## Context

Renamed `docs/regime-taxonomy.jsonld` to follow `NNN-kebab-case-vNN` naming convention (`docs/010-regime-taxonomy-v01.json`).

## Changes Made

- Renamed file and updated internal `url` field.
- Updated references in: `capture_market.py`, `predictions_loader.py`, `intraday-pipeline.yml`, data files, and documentation.

## Impact

- Adherence to project naming conventions.
- CI pipeline verified passing (all steps).

## Next Steps

- Monitor upcoming Node.js 20 deprecation.
