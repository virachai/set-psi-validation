# Validation Directory

Stores the results of the PSI validation engine.

## Naming Convention

- Files follow the pattern `YYYY-MM-DD-HHMMSS-{session}.json`.
- `session` is one of `am`, `pm`, `full_day`.
- A file is written only once its session's market outcome exists (`am` → noon capture, `pm`/`full_day` → ATC capture); nothing is written before that.

## Schema

Each file is a **JSON‑LD** document containing:

- `@context`
- `@type`
- `observationDate`
- `observationAbout` (references to the corresponding prediction and market‑data files)
- `measuredProperty`
- `variableMeasured` (e.g., `Is Correct`)
- `marginOfError`
- `predictedRegime`
- `actualRegime`
- `isCorrect`
- `deviationScore`

> **Note**: Validation entries are immutable once written. New validation runs generate new files; never edit existing ones.
