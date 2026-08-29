# Predictions Directory

This folder contains **JSON-LD** snapshots of PSI predictions captured throughout each trading day.

## Naming Convention

- Files follow the pattern `YYYY-MM-DD-HHMMSS-{session}.json` where `session` is one of:
  - `am`
  - `pm`
  - `full_day`
- Example: `2026-08-03-022804-am.json`

## Schema

All files conform to the [Schema.org Observation](https://schema.org/Observation) model and include:

- `@context`
- `@type`
- `name`
- `observationDate`
- `measuredProperty`
- `variableMeasured`
- `additionalProperty`
- `timestamp`
- `date`
- `predictedRegime`
- `psiScore`
- `modelId`
- `session`

## Usage

These files are consumed by the **validation engine** to compare against actual market outcomes stored in the `validation/` directory.

> **Note**: Keep this directory version‑controlled; never delete historical files as they are required for audit trails.
