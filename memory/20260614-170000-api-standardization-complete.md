# API Standardization Complete

## Metadata

- **Date:** 2026-06-14
- **Author:** Gemini CLI
- **Status:** COMPLETED

## Context

PSI API now returns schema.org `Observation` consistently across Lambda and RapidAPI. RapidAPI acts as a public gateway, Lambda handles PSI computation, and Python script performs schema.org transformation.

## Changes Made

- Modified Lambda to return `Observation` directly (no `{status, ...}` wrapper).
- Extended `calculatePSI()` with diagnostics (`_diagnostics`).
- Updated `predictions_loader.py` to detect and passthrough native schema.org responses.
- Added tests for schema.org passthrough and backward compatibility.

## Impact

- Consistent data format (JSON-LD `Observation`).
- Simplified API consumption.
- Maintained backward compatibility.

## Next Steps

- Continue pipeline integration monitoring.
