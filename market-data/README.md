# Market‑Data Directory

Contains raw intraday market snapshots for the SET market.

## Naming Convention

- Files follow the pattern `YYYY-MM-DD-HHMMSS.json`.
- No session suffix is used because these are daily aggregates.

## Schema

Each file is a **JSON‑LD** document describing the market data observed at a given timestamp. Fields generally include:

- `@context`
- `@type`
- `name`
- `observationDate`
- `variableMeasured` (e.g., ATO price, ATC price, volatility)

> **Note**: Historical market data is immutable. Do **not** edit existing files; add new files for new days.
