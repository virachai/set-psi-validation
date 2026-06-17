---
name: cron-interval-idempotent
description: Changed cron to */30 min interval with range-based time windows and idempotent scripts to tolerate GitHub Actions queue delays
type: project
---

# Cron Interval & Idempotent Scripts

**Problem:** GitHub Actions free-plan scheduled workflows experience unpredictable queue delays (observed up to 5+ hours). Exact-hour cron + exact-hour matching in Determine Step meant delayed runs always fell through to `step=none`.

**Solution — three changes:**

## 1. Single `*/30` cron replaces 5 exact-hour schedules

- Before: 5 cron entries (`0 2`, `0 3`, `0 7`, `30 9`, `0 10`) — one per market step
- After: `*/30 1-11 * * 1-5` (every 30 min, 08:00-18:59 ICT)
- Why: Redundant triggers guarantee a run lands in the correct time window even with hours of delay

## 2. Range-based time windows

- Before: exact hour match (`$H_ICT == "09"`, `$H_ICT == "10"`, etc.)
- After: range-based (`-ge 8 && -le 9`, `-ge 10 && -le 11`, etc.)
- Windows: prediction-am 08-09, ato 10-11, prediction-pm 12-15, atc 16, validation 17-18 ICT

## 3. Idempotent scripts (no dup files despite redundant triggers)

- `predictions_loader.py`: checks `predictions/YYYY-MM-DD-*-session.json` before API call → skip if exists
- `capture_market.py`: checks existing data for `atoPrice` (ATO mode) or `status=complete` (ATC mode) → skip if exists
- `validation_engine.py`: checks `validation/YYYY-MM-DD-*.json` before running → skip if exists (`update_aggregate_metrics` still runs to refresh metrics.json)

**Usage impact:** ~37 min/month of GitHub Actions free tier (of 2,000 min quota)

**Files modified:**

- `.github/workflows/intraday-pipeline.yml`
- `scripts/python/predictions_loader.py`
- `scripts/python/capture_market.py`
- `scripts/python/validation_engine.py`
