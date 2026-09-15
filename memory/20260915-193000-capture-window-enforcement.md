---
name: capture-window-enforcement
description: Captures are guarded by a two-sided CAPTURE_WINDOWS table; pmopen opens at 14:30 not 14:00, and backfills must be stamped.
metadata:
  pinned: false
---

`capture_market.py` defines `CAPTURE_WINDOWS`, a table of the ICT window in which each
mode's quote is a truthful stand-in for the snapshot it claims to be, enforced by
`_assert_in_window` on the live *and* manual `--price` paths:

| mode | window (ICT) | why |
| :--- | :--- | :--- |
| `ato` | ≥ 10:00 | reads the provider's session-open field, valid all day — no cutoff |
| `noon` | 12:30 – 14:00 | reads the *current* quote, so both bounds matter |
| `pmopen` | 14:30 – 16:30 | reads the *current* quote, so both bounds matter |
| `atc` | ≥ 16:30 | reads the post-close price, valid for the rest of the day — no cutoff |

**The 14:00 vs 14:30 distinction is the easy mistake.** `SET_AFTERNOON_PREOPEN_ICT`
(14:00) is when the pre-open call auction starts, and is the *noon cutoff*.
`SET_AFTERNOON_OPEN_ICT` (14:30) is when the afternoon continuous session opens, and is
the *pmopen lower bound*. Reusing one constant for both lets the `:03` cron record a
14:03 pre-open quote as the PM open — exactly the class of corruption the guards exist
to stop. Keep them separate, and keep `intraday-pipeline.yml`'s decider buckets inside
the windows (its `pmopen` bucket also stops at 16:20, because a bucket emitted at 16:29
plus a cold `uv` install would cross the 16:30 cutoff mid-run).

**Provenance is mandatory for anything not captured live.** A record written outside its
window carries `windowGuardBypassed: true` (via `PSI_BYPASS_WINDOW_GUARD` and
`_mark_bypass`); a record rebuilt by `backfill_market_data.py` carries `backfilledFrom`.
Both exist because a backfilled file's filename time is the window it *represents*, not
the moment it was written, so without a stamp it is indistinguishable from a live capture.

**Deriving a session's regime pulls in more inputs than it looks.** The `atc` record
embeds `atoPrice` and `pmOpenPrice`, so its `returnPct` and `afternoonReturnPct` are
poisoned by a bad `ato` or `pmopen` capture. When invalidating data, follow
`SESSION_SOURCE_MODES` in `quarantine_out_of_window.py`: `am` depends on {ato, noon},
`pm` on {pmopen, atc}, `full_day` on {ato, atc}.
