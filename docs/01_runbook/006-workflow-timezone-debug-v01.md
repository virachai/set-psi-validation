# Runbook: Workflow Timezone & Scheduling Debug (v01)

- **Purpose**: Diagnostic and recovery for timezone discrepancies and scheduling delays.
- **Applies to**: `.github/workflows/intraday-pipeline.yml`
- **Context**: Dual-Zone (ICT/UTC) detection and Lookahead Bias protection.
- **Last Updated**: 2026-06-17

---

## 1. ICT Market Schedule Reference

The pipeline is synchronized with the **Stock Exchange of Thailand (SET)** schedule (ICT Time):

Scheduled retries fire throughout each operational window; the step-decider in `intraday-pipeline.yml` picks the step from ICT time. The scheduler is intentionally redundant because GitHub Actions can delay scheduled jobs:

| Step                         | Detection Window (ICT) | UTC                    |
| :--------------------------- | :--------------------- | :--------------------- |
| **Prediction (Full Day)**    | 05:00–09:59            | 22:00–02:59 (prev day) |
| **ATC Capture + Validation** | 16:45–23:59            | 09:45–16:59            |

---

## 2. Diagnostic Log Reading

Every workflow run starts with a **Determine Step** phase. Open the logs for this step to diagnose:

### 2.1. Normal Logs (Target hit)

```text
System Time (UTC): Wed Jun 17 01:03:05 UTC 2026
Market Time (ICT): Wed Jun 17 08:03:05 +07 2026
Verification -> ICT: 08 | UTC: 01
(Step matches prediction-full-day)
```

### 2.2. Ghost Run Logs (Outside window)

```text
Verification -> ICT: 22 | UTC: 15
(Step is set to none)
```

_Note: This is normal for Push events or manual runs outside schedule. The workflow will complete as "Success" by skipping functional steps._

### 2.3. Lookahead Bias Warning

If you see `[WARN] Lookahead Bias: full_day prediction captured at 10:03 ICT`:

- **Cause**: The capture script ran after the session cutoff.
- **Impact**: The prediction for that session is skipped to ensure data integrity.
- **Fix**: Check if GitHub cron was delayed or if a manual run was triggered late.

---

## 3. Failure Scenarios & Fixes

### 3.1. "Ghost" Failures (CI showing Red)

- **Symptom**: Step decider shows `step=none` but Commit step fails.
- **Root Cause**: Unstaged changes (usually logs) detected by `git commit`.
- **Fix**: The workflow now uses `git diff --staged --quiet`. Ensure your local `intraday-pipeline.yml` includes this safety guard.

### 3.2. Scheduled Job Didn't Run

- **Symptom**: No workflow run appears in the Actions tab at the expected time.
- **Root Cause**: GitHub cron engine delay (normal up to 15-20 mins) or cron misconfiguration.
- **Fix**:
  1. Wait 15 minutes.
  2. If still no run, perform **Manual Recovery (Section 4)**.

### 3.3. Job Ran but Skipped Everything (`step=none`)

- **Symptom**: Job ran at a time that does not match the expected bucket.
- **Root Cause**: Runner system clock drift or incorrect TZ environment.
- **Fix**: Check `H_UTC` in logs. If UTC is correct, the Dual-Zone logic will still catch it. If both are wrong, verify the `Asia/Bangkok` timezone string in the workflow file.

---

## 4. Manual Recovery Procedure

If a scheduled step was missed or failed, **do not run `all`**. Run the specific step:

1. Go to **Actions** tab -> **Intraday Market Cycle**.
2. Click **Run workflow**.
3. Select the branch (usually `main`).
4. Select the specific **Step to run** (e.g., `prediction-full-day`, `atc-and-validate`).
5. Click **Run workflow**.

_Manual selection bypasses the hourly time-check, allowing recovery at any time._

---

## 5. Maintenance: Adjusting Cutoffs

If the market schedule changes, update these in `scripts/python/predictions_loader.py`:

- `PSI_OPEN_FULL_DAY` / `PSI_CUTOFF_FULL_DAY`: Default `09:00:00` / `10:00:00`

And update the `step-decider` in `.github/workflows/intraday-pipeline.yml`.

---

**Status**: Operational
**Governance**: Compliant with "Lean PSI Validator" principles.
