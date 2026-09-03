# RFC 016: Four-Session Market Data Timing (Morning Open → Lunch Break → Afternoon Open → Close)

> **Status**: Implemented (2026-09-03) — `noon` and `pmopen` modes shipped in `capture_market.py` and `.github/workflows/intraday-pipeline.yml`; see RFC 017 for the validation-side wiring.
> **Scope**: `market-data/` capture timing, `capture_market.py` modes, `.github/workflows/intraday-pipeline.yml`
> **Governance**: Lean PSI Validator (Truth Metric Calculation only)

---

## 1. Problem

SET trades in two distinct sessions with a lunch break in between:

| Session | ICT Time |
|---|---|
| Morning | 10:00 – 12:30 |
| Lunch Break | 12:30 – 14:30 |
| Afternoon | 14:30 – 16:30 |
| ATC (close) | ~16:30 – 16:40 |

The current pipeline only captures two points — `ato` (morning open, ~10:00) and `atc` (final close, ~16:30). It has no record of the **morning-session close (lunch break price)** or the **afternoon-session open**, so intraday regime derivation cannot distinguish "reversed direction over lunch" from "continued trend" — a gap the user flagged: *market-data currently only spans open→close, not open→lunch, then afternoon-open→close.*

## 2. Proposed Timing Design

Add two new capture modes, bringing the daily cycle to four price snapshots:

| Mode | Trigger (ICT) | Represents | New? |
|---|---|---|---|
| `ato` | 10:00 | Morning session open | existing |
| `noon` | 12:30 | Morning session close (lunch break) | **new** |
| `pmopen` | 14:30 | Afternoon session open | **new** |
| `atc` | 16:30–16:40 | Afternoon session close (final) | existing |

Filenames follow the existing convention from `memory/20260828-113000-artifact-naming-convention.md` — `{YYYY-MM-DD}-{HHMMSS}-{suffix}.json` with ICT time and suffix = mode name:

```
market-data/2026-09-03-100000-ato.json
market-data/2026-09-03-123000-noon.json
market-data/2026-09-03-143000-pmopen.json
market-data/2026-09-03-163000-atc.json
```

## 3. Workflow Step-Decider Changes (design only)

Extend the existing range-based decision ladder in `intraday-pipeline.yml` (`step-decider`):

```text
H:M ICT          → step
08:00–09:59      → prediction-am
10:00–12:29      → ato
12:30–12:44      → noon        (new window, 15 min tolerance)
12:45–14:29      → prediction-pm
14:30–14:44      → pmopen      (new window, 15 min tolerance)
14:45–16:44      → atc         (existing "atc" trigger moves earlier to 16:45 gate stays same)
16:45–16:59      → atc
17:00+           → validation
```

Add matching `workflow_dispatch` choices: `noon`, `pmopen`.

## 4. Derived Metrics Enabled

With four snapshots, the validation layer can compute (Truth Metric Calculation, in scope per lean governance):

- **Morning return** = `(noon - ato) / ato`
- **Lunch gap** = `(pmopen - noon) / noon` — reveals overnight-style sentiment shift within the same day
- **Afternoon return** = `(atc - pmopen) / pmopen`
- **Full-day return** = `(atc - ato) / ato` (existing)

This lets `predictions/*-am.json` be validated against the **morning window** (`ato → noon`) and `predictions/*-pm.json` against the **afternoon window** (`pmopen → atc`) instead of both being checked against the same full-day outcome — directly improving AM/PM prediction-accuracy granularity already partially built in `validation_engine.py`'s three-window analysis (see `memory/20260615-195500-validation-engine-three-window.md`).

## 5. Compatibility Notes

- `load_existing()` in `capture_market.py` already globs by `{date}-*-{mode}.json`, so adding two new suffixes needs no change to the lookup pattern — only two new `handle_noon` / `handle_pmopen` mode branches (implementation deferred; this RFC is spec-only per the Never-Implement mandate).
- `regime_rules.derive_actual_regime` currently takes ATO/ATC only; deriving per-window regimes is a separate, later RFC — out of scope here.
- No new suffix breaks the existing `{date}-*.json` glob used by dashboards/reports.

## 6. Out of Scope (per Lean PSI Validator governance)

- No new infrastructure, queues, or cross-repo systems.
- No ML/walk-forward pipeline for the new windows — plain return % only.
- Implementation (code changes to `capture_market.py`, workflow YAML) is **not** performed by this RFC; it requires explicit approval to proceed to a build task.

---

**Effective Date**: 2026-09-03
