---
name: 20260828-113000-artifact-naming-convention
description: Unified data artifact naming rule {YYYY-MM-DD}-{HHMMSS}-{suffix}.json across market-data, predictions, reports.
type: feedback
---

**Rule:** All data artifact directories use one filename rule: `{YYYY-MM-DD}-{HHMMSS}-{suffix}.json` with ICT time.

| Dir | Suffix | Example |
|---|---|---|
| market-data/ | mode (ato, atc) | `2026-08-28-000000-ato.json` |
| predictions/ | session (am, pm, full_day) | `2026-08-28-022759-am.json` |
| reports/ | metrics | `2026-08-28-223533-metrics.json` (+ `metrics.json` latest copy for dashboard) |
| validation/ | prediction file_id | `2026-08-28-022759-am.json` |

**Why:** `reports/` previously used `metrics-YYYYMMDD-HHMMSS.json` (compact date, artifact-prefix) — the odd one out. Aligning keeps the "find latest file by glob `{date}-*.json`" logic working everywhere (find_latest_file / find_latest_prediction_file).

**How to apply:**
- Timestamps in filenames and `datePublished` must be ICT (UTC+7), never UTC — the old `datetime.now(timezone.utc)` + `+07:00` label was a 7-hour-off bug (fixed in validation_engine.py).
- All schema.org artifacts carry `measuredProperty` (DefinedTerm) — metrics Dataset now includes `Regime Prediction Accuracy`.
- Historical `metrics-*.json` files were left as-is; only new writes follow the rule.
