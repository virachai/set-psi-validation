# RFC 019 — Capture Window Enforcement & Truth-Layer Rebuild

> **Status**: Implemented
> **Date**: 2026-09-15
> **Partially superseded by**: RFC 020 (single daily cycle). The `ato`, `noon` and `pmopen`
> modes described below were removed; only the `atc` window (>= 16:30 ICT) and the
> backfill provenance stamps remain in force. RFC 016/017 were deleted with that rollback.

---

## 1. Problem

Every `ato`, `noon`, and `pmopen` capture from 2026-09-09 to 2026-09-15 was written at
~09:28 ICT — before the windows they claimed. `market-data/2026-09-15-092805-noon.json`
was stamped 09:28:05 while declaring `observationPeriod: 10:00 → 12:30`.

Two guards were missing and one path was unguarded:

- `_assert_before_cutoff` enforced only an **upper** bound, so a 09:28 run passed
  the "before 14:00" test and recorded a 09:28 live quote as the 12:30 noon close.
- `_capture_ato` had **no** time guard at all.
- `workflow_dispatch` with `step=all` bypasses the workflow's time-range chain
  entirely, which is how the bad runs fired.

Impact: `returnPct` and `volatilityIndex` were computed from prices that never
belonged to their window, so `derive_actual_regime` labelled the wrong regime and
`reports/metrics.json` scored the PSI hypothesis against fiction. The stored ATO
for 2026-09-15 was 1600.87 against a true open of 1587.35 — a 13.5-point error.
Separately, all `pm` predictions were timestamped 09:28 ICT, before their own
13:00 window opens.

## 2. Decision

### 2.1 Window table as the single source of truth

`CAPTURE_WINDOWS` in `scripts/python/capture_market.py` now declares the valid ICT
window per mode, and `_assert_in_window` enforces both bounds:

| mode     | window (ICT)  | cutoff rationale                                            |
| :------- | :------------ | :---------------------------------------------------------- |
| `ato`    | ≥ 10:00       | reads the provider's *session-open* field, valid all day     |
| `noon`   | 12:30 – 14:00 | reads the *current* quote — both bounds required             |
| `pmopen` | 14:30 – 16:30 | reads the *current* quote — both bounds required             |
| `atc`    | ≥ 16:30       | reads the post-close price, valid for the rest of the day    |

`pmopen` opens at **14:30**, not 14:00. `SET_AFTERNOON_PREOPEN_ICT` (14:00) is the
noon *cutoff* — the start of the pre-open call auction — while the afternoon
continuous session opens at 14:30. An earlier draft of this change reused the 14:00
constant for both, which would have let the `:03` cron record a 14:03 pre-open quote
as the PM open: the very defect these guards exist to prevent. The two bounds are now
distinct constants (`SET_AFTERNOON_PREOPEN_ICT` and `SET_AFTERNOON_OPEN_ICT`), and
`intraday-pipeline.yml`'s decider emits `pmopen` only from 14:30.

**Deviation from the original plan**: `ato` was planned with a 10:30 cutoff. It has
none, because `_fetch_live_prices` returns the provider's daily-bar `Open` for
`ato`, which does not decay through the session. A cutoff would only have produced
spurious failures whenever the 10:03 scheduled run was delayed.

### 2.2 Auditable bypass

`PSI_BYPASS_WINDOW_GUARD=true` downgrades the failure to a warning and stamps
`"windowGuardBypassed": true` on the record, so a backfill is always
distinguishable from a live capture. `python-quality.yml` fails the build if the
flag is set, mirroring the existing `PSI_BYPASS_LOOKAHEAD` gate.

### 2.3 One clock for all artifacts

`predictions_loader.save_snapshot` now converts to ICT before formatting the
filename (via the new `_to_ict` helper, which also backs `validate_timestamp`).
Previously `predictions/` and `validation/` encoded UTC while `market-data/`
encoded ICT, making same-instant files appear seven hours apart. Existing
prediction and validation files were renamed accordingly.

### 2.3a Workflow alignment

Every ICT bucket `intraday-pipeline.yml`'s `Determine Step` chain can emit now lands
inside the target mode's window. Two decider changes were required: `pmopen` starts at
14:30 (above), and it stops at **16:20** rather than 16:30, because a bucket emitted at
16:29 plus a cold `uv` dependency install (20–60 s) would re-read the clock past the
16:30 cutoff and raise mid-run.

`step=all` is now self-limiting: at any instant at most one capture window is open, so
the other three raise and are absorbed by the `continue-on-error` already present on
those steps (`intraday-pipeline.yml:111,120,139,148`). A `step=all` dispatch at 09:28 —
the exact trigger that produced the corrupt data — now writes nothing instead of writing
four wrong records. Scheduled and push runs still fail hard, which is the desired signal
if a bucket ever drifts out of alignment.

### 2.4 Quarantine, not deletion

`scripts/python/quarantine_out_of_window.py` moves offenders to `<dir>/quarantine/`,
driven by the same `CAPTURE_WINDOWS` / `MARKET_WINDOWS` tables the pipeline enforces,
so the check cannot drift from the guards. It covers market-data captures, predictions,
and any validation record derived from either.

`quarantine/` is **gitignored**. The pre-quarantine artifacts are already committed at
`96ec15f`, so re-committing them would store known-bad data twice and leave fiction in
the directories the dashboard reads. `git show 96ec15f:market-data/<file>` recovers any
of them.

**Deviation from the original plan**: the plan assumed `full_day` validations
could be kept because ATC was captured honestly. They could not — the `atc`
record embeds `atoPrice` and `pmOpenPrice`, so its `returnPct` and
`afternoonReturnPct` were derived from the bad captures too. All 14 validation
records were quarantined, and `SESSION_SOURCE_MODES` encodes these input
dependencies so the check stays correct.

### 2.5 Backfill from intraday bars

`scripts/python/backfill_market_data.py` rebuilds past captures from Yahoo 30-minute
bars, which carry their own ICT timestamps:

- `ato` = open of the 10:00 bar
- `noon` = close of the 12:30 bar
- `pmopen` = open of the 14:30 bar
- `atc` = the **already-captured** `atcPrice` from the existing post-close record

ATC is deliberately not re-derived from bars: the last 30m bar ends at 16:30 and so
excludes the closing auction, and Yahoo returns no historical daily series for
`^SET.BK`. The live `atc` captures were taken after 16:30 and their prices are
genuine, so the backfill preserves them and only recomputes the returns that were
poisoned by bad ATO/PM-open inputs.

Every backfilled record carries `"backfilledFrom": "yahoo-30m"` (the ATC record,
which keeps its genuine captured price, reads `"yahoo-30m+captured-atc"`). Without it a
backfill would be byte-indistinguishable from a live capture, since its filename time is
the window it represents rather than the moment it was written — `_mark_bypass` plays the
same role for an out-of-window live capture.

Records are written through the same `handle_*` functions as the live path, so
schema and regime derivation stay single-sourced. `save_market_data` gained an
optional `captured_at` so a backfilled file is stamped with the window time it
actually represents. Superseded records move to `market-data/quarantine/superseded/`
because every resolver picks `sorted(glob(...))[-1]`, so leaving them in place
would let a stale record win on filename sort order.

## 3. Outcome

`market-data/` now holds 6 dates × 4 windows, each stamped at its true window time,
and `quarantine_out_of_window.py` reports clean. Rebuilt metrics:

| window     | samples | accuracy |
| :--------- | ------: | -------: |
| `am`       |       5 |     0.60 |
| `full_day` |       5 |     0.60 |
| `pm`       |       0 |      n/a |

`pm` is empty because all four `pm` predictions were made at 09:28 ICT, before
their 13:00 window. Predictions come from the PSI engine and have no history API,
so **PM history is not recoverable** — that window restarts from the next live run.
The dashboard should read an empty `pm` row as "no data yet", not as 0% accuracy.

Prediction filenames also moved from UTC to ICT on this date, so the same instant that
was written `022759` is now written `092759`. RFC 016 §Filenames already specified ICT;
this brings predictions into compliance, at the cost of a one-time discontinuity in the
historical filename series.

## 4. Known gaps (not addressed here)

- **`Unclassified` regimes.** 2026-09-15 AM returns −0.18% (inside the ±0.5%
  sideways band) with volatility 0.0079 against a 0.00786 threshold. Because
  `derive_actual_regime` requires `volatility < threshold` for `Sideways`, a
  0.00004 overshoot drops it to `Unclassified`. Changing that boundary is a
  hypothesis decision, not a bug fix, so the rules are untouched.
- **`audit_truth_layer.py` reports AM predictions as orphans.** It matches
  predictions against the full-day `atc` record only and has no knowledge of the
  `noon` file that RFC 017 introduced for AM scoring. Pre-existing.
- **Duplicate `date+window` files** are still possible in principle; resolvers
  remain last-wins. The backfill's supersede step handles it for backfills only.

---

**Effective Date**: 2026-09-15
