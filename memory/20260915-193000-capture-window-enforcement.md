---
name: capture-window-enforcement
description: The single atc capture is guarded by CAPTURE_WINDOWS (>= 16:30 ICT); records not captured live must carry a provenance stamp.
metadata:
  pinned: false
---

`capture_market.py` defines `CAPTURE_WINDOWS`, the ICT window in which a mode's quote is a
truthful stand-in for the snapshot it claims to be, enforced by `_assert_in_window` on the
live *and* manual price paths. Since RFC 020 (single daily cycle) the only mode is `atc`,
valid at/after 16:30 ICT with no upper cutoff: it reads the day's open and post-close
price in one call, and both stay correct for the rest of the day. The `ato`, `noon` and
`pmopen` windows from RFC 019 were removed along with those modes.

**Provenance is mandatory for anything not captured live.** A record written outside its
window carries `windowGuardBypassed: true` (via `PSI_BYPASS_WINDOW_GUARD` and
`_mark_bypass`); a record rebuilt by `backfill_market_data.py` carries `backfilledFrom`.
Both exist because a backfilled file's filename time is the window it *represents*, not
the moment it was written, so without a stamp it is indistinguishable from a live capture.
CI fails if either bypass is enabled.
