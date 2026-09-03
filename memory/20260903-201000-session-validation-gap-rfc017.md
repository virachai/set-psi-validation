---
name: 20260903-201000-session-validation-gap-rfc017
description: Discovered am/pm/full_day validation records all compare against the same full-day market file; designed RFC 017 fix (spec only).
type: feedback
---

**Finding:** `validation_engine.py::run_daily_validation()` calls `find_latest_market_file()` once per date and reuses that single file (the day's `atc` snapshot) for all three prediction sessions (`am`, `pm`, `full_day`). Confirmed on 2026-09-03: `validation/2026-09-03-022758-am.json` and `-pm.json` both cite `market-data/2026-09-03-092804-atc.json` in `observationAbout` and produce identical `actualRegime`. Session-level accuracy in `reports/metrics.json` is therefore currently indistinguishable from full-day accuracy — the three-window schema exists but isn't backed by three-window market truth.

**Decision:** Wrote `docs/02_rfc/017-rfc-session-aware-validation-alignment-v01.md` (addendum to RFC 016's proposed `noon`/`pmopen` market-data capture modes) specifying a `find_market_window(date_str, session)` helper that resolves `am → (ato, noon)`, `pm → (pmopen, atc)`, `full_day → (ato, atc)` (unchanged), with fallback to the full-day pair when `noon`/`pmopen` files don't exist for a date — preserving current behavior for all historical data. `regime_rules.derive_actual_regime()` needs no change; it already accepts arbitrary price pairs.

**Why this matters for future sessions:** Per this repo's Outcome-First / Never-Implement governance, RFC 016 and 017 are spec-only — no code was changed. If asked to implement per-session market validation, start from RFC 017's `find_market_window()` design rather than re-deriving the mapping, and confirm RFC 016's `noon`/`pmopen` capture modes are implemented first (they are a prerequisite).
