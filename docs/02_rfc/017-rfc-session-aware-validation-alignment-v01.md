# RFC 017: Session-Aware Validation Alignment (`predictions/` ↔ `market-data/` ↔ `validation/` ↔ `reports/`)

> **Status**: Implemented (2026-09-03) — `_resolve_market_outcome()` shipped in `validation_engine.py`, replacing the design's proposed `find_market_window()` name with an equivalent (path, actual_regime) resolver.
> **Scope**: `validation_engine.py`
> **Governance**: Lean PSI Validator (Comparison + Truth Metric Calculation only)

---

## 1. Problem

`predictions/` already models three forecast windows per day — `am`, `pm`, `full_day` (see `predictions/README.md`, enforced by `SESSIONS = ("am", "pm", "full_day")` in `validation_engine.py`). But `run_daily_validation()` resolves market truth with `find_latest_market_file(MARKET_DATA_DIR, date_str)`, which returns **one file for the whole day** (the latest `atc` snapshot) and reuses it for every session's comparison.

Concrete evidence from 2026-09-03:

- `validation/2026-09-03-022758-am.json` → `observationAbout` cites `market-data/2026-09-03-092804-atc.json`, `actualRegime: "Bearish"`.
- `validation/2026-09-03-022758-pm.json` → cites the same `market-data/2026-09-03-092804-atc.json`, same `actualRegime: "Bearish"`.
- `validation/2026-09-03-022758-full_day.json` → same file, same result.

All three records derive from the identical `(ato, atc)` price pair via `regime_rules.derive_actual_regime()`. So `am` and `pm` accuracy in `reports/metrics.json`'s per-session grouping (`sdf = df[df["session"] == s]`) is mathematically guaranteed to equal `full_day` accuracy — session-level validation is not actually measuring session-level prediction quality today.

This is the natural follow-on to RFC 016 (`docs/02_rfc/016-rfc-four-session-market-data-timing-v01.md`), which proposed two new `market-data/` capture modes — `noon` (12:30, morning close) and `pmopen` (14:30, afternoon open) — but did not wire them into the validation layer. This RFC closes that gap.

## 2. Target Alignment

| Folder | Key | Session → data mapping |
|---|---|---|
| `predictions/` | `{date}-{time}-{session}.json`, session ∈ {am, pm, full_day} | — |
| `market-data/` | `{date}-{time}-{mode}.json`, mode ∈ {ato, noon, pmopen, atc} (noon/pmopen added by RFC 016) | — |
| `validation/` | `{date}-{time}-{session}.json` (mirrors prediction `file_id`) | `am` → (`ato`, `noon`) · `pm` → (`pmopen`, `atc`) · `full_day` → (`ato`, `atc`), unchanged |
| `reports/` | `metrics.json` | per-session grouping already exists; becomes meaningful once rows differ |

## 3. Design (spec only — no code changes in this RFC)

### 3.1 `find_market_window(date_str: str, session: str) -> tuple[str, str] | None`

Replaces the single-file `find_latest_market_file()` call for `am`/`pm` sessions in `run_daily_validation()`. Returns a pair of market-data **file paths** `(before, after)` to feed `derive_actual_regime()`, resolved per session:

```
session == "am"        → (find_mode_file(date, "ato"),    find_mode_file(date, "noon"))
session == "pm"         → (find_mode_file(date, "pmopen"), find_mode_file(date, "atc"))
session == "full_day"   → (find_mode_file(date, "ato"),    find_mode_file(date, "atc"))
```

**Fallback rule** (preserves current behavior for any date lacking the new snapshots): if either half of an `am`/`pm` pair is missing, fall back to the `full_day` pair — i.e. behave exactly as today until `noon`/`pmopen` files exist for that date. This mirrors the existing fallback pattern already used in `_resolve_prediction_path()` for `full_day` predictions, so no new fallback idiom is introduced.

### 3.2 `derive_actual_regime()` — reused unchanged

`regime_rules.derive_actual_regime(ato_price, atc_price, volatility_index, threshold_mean)` already accepts arbitrary price-pair arguments. No signature or threshold change is needed — `run_daily_validation()` simply calls it once per session with the window-appropriate price pair instead of always the full-day pair. Regime thresholds and `VALID_REGIMES` in `regime_rules.py` are out of scope for this RFC.

### 3.3 `_build_validation_record()` — `observationAbout` traceability fix

Currently every record's `observationAbout` cites only the single latest market file, regardless of session. Update it to list the two market-data files actually used for that session's window (e.g. `market-data/*-ato.json` + `market-data/*-noon.json` for an `am` record), so the JSON-LD record is truthful about its evidentiary basis.

## 4. Backward Compatibility

- Historical dates (all data before this design ships) have no `noon`/`pmopen` files → fallback rule (§3.1) keeps `run_daily_validation()` producing identical output to today. No backfill required.
- `reports/metrics.json` schema is unchanged — its existing per-session grouping starts reflecting genuine per-window accuracy automatically once §3.1–3.2 are implemented; no aggregation-layer changes needed.
- `validation/` filename convention (`{date}-{time}-{session}.json`) is unchanged.

## 5. Out of Scope

- Implementation of `find_market_window()` or any code change to `validation_engine.py` — this RFC is spec-only per the Never-Implement mandate; a follow-up build task requires separate approval.
- Changes to regime-derivation thresholds or `VALID_REGIMES` taxonomy.
- Backfilling `noon`/`pmopen` market-data for historical dates.
- Implementation of RFC 016's capture-mode changes themselves (prerequisite, tracked separately).

---

**Effective Date**: 2026-09-03
