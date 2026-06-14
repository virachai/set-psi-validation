# Runbook: Troubleshooting Guide (v01)

- **Purpose**: Diagnostic and recovery procedures for PSI validation pipeline anomalies.
- **Applies to**: `set-psi-validation` pipeline
- **Last Updated**: 2026-06-14

---

## 1. Diagnostic Framework

When the pipeline fails, follow these steps:

1. **GitHub Actions Logs**: Open the failed job → locate step → expand logs.
2. **Error Tags**: Look for:
   - `[ERROR]`: Critical failure (API errors, script crashes).
   - `[SKIP]`: Expected skipping (Non-market days, API Auth issues).
   - `[WARN]`: Non-critical warnings (Unknown regimes).

## 2. Common Failure Scenarios

### 2.1. API Authentication Failed (401/403)

- **Cause**: Secrets in GitHub Actions are missing, expired, or incorrect.
- **Fix**:
  1. Verify Secrets in **Repo Settings -> Secrets and variables -> Actions**.
  2. If incorrect, update keys.
  3. Re-run the failed workflow step.

### 2.2. Missing Market Data (Skipped)

- **Cause**: Script detected that SET market was closed or API returned no data.
- **Action**:
  1. Check `docs/FLOW.md` for SET market schedule.
  2. If data _should_ exist, verify `capture_market.py` logs for API URL availability.

### 2.3. Pipeline Failures in `python-quality`

- **Cause**: Code does not meet formatting (`black`) or linting (`ruff`) standards.
- **Fix**:
  1. Run `uv run ruff check scripts/ tests/` locally.
  2. Fix errors or run `uv run black scripts/ tests/`.
  3. Commit and push the fix.

## 3. Recovery Procedures

### Scenario A: Re-running a specific date

If data was partially captured or corrupted:

1. Delete the affected JSON file in `market-data/` or `predictions/`.
2. Trigger the workflow manually via **Actions** tab with the appropriate `step` input.

### Scenario B: Data Enrichment Failure

If `jsonld_enricher.py` fails:

1. The file might be malformed JSON.
2. Run `uv run scripts/python/jsonld_enricher.py --validate-only` to locate the culprit file.
3. Fix the JSON structure and re-run.

---

**Status**: Operational
**Governance**: Compliant with "Lean PSI Validator" principles.
