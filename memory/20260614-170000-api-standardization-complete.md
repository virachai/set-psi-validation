---
name: api-standardization-complete
description: PSI API now returns schema.org Observation consistently across Lambda and RapidAPI
type: project
---

# API Standardization Complete

## Work Done

1. **Lambda modified** to return schema.org `Observation` directly:
   - `createResponse` updated with `isSchemaOrg` mode → `Content-Type: application/ld+json`, body is raw Observation (no `{status, ...}` wrapper)
   - `calculatePSI()` extended with `_diagnostics` (avgEquityChange, dxyChange, thbChange)
   - Handler builds full Observation: `@context`, `@type`, `observationDate`, `measuredProperty` (link to regime taxonomy), `variableMeasured` (PSI Score, Predicted Regime, VIX Level), `additionalProperty` (diagnostics)
   - `console.time`/`console.timeEnd` for timing → CloudWatch logs only, not in response

2. **`predictions_loader.py` `build_snapshot()`** updated:
   - Detects native schema.org response (`@type: "Observation"`) → passthrough + backward-compat fields
   - Legacy RapidAPI format still supported as fallback transform

3. **Tests** added/updated:
   - 3 new Python tests for schema.org passthrough path (passthrough, additionalProperty preservation, regime normalisation)
   - 8 Node.js Lambda tests updated to verify schema.org Observation format, cache hits, diagnostics, auth

4. **Architecture decision**: Use RapidAPI as public gateway + `predictions_loader.py` transform middleware. Lambda kept as internal reference.

## Key Files

- `.tmp/nodejs/101_native-lambda-nodejs/lambda_function.js`
- `scripts/python/predictions_loader.py`
- `tests/python/test_predictions_loader.py`
- `.tmp/nodejs/101_native-lambda-nodejs/test_lambda.js`

## Why: RapidAPI provides auth/rate-limit layer, Lambda provides PSI computation, Python script provides schema.org transform. Each layer does one thing.
