# Runbook: Operations & Maintenance (v01)

- **Purpose**: Centralized guide for daily monitoring, troubleshooting, and dashboard maintenance.
- **Applies to**: `set-psi-validation` pipeline
- **Last Updated**: 2026-06-14

---

## 1. Daily Operations & Monitoring

The system operates autonomously. Your role is primarily observational.

### Monitoring Checklist

1. **GitHub Actions**: Daily check of the `Intraday Market Cycle` action.
   - Status should be `Success`.
   - A `Success` with `[SKIP]` messages on non-market days is normal.
2. **Data Integrity**:
   - Check `predictions/`, `market-data/`, and `validation/` folders for new JSON files dated for the current trading day.
   - Files are timestamped `YYYY-MM-DD-HHMMSS.json`.
3. **Metrics Aggregation**:
   - Verify `reports/metrics.json` is updated with the latest validation results.

---

## 2. Troubleshooting Guide

### Common Issues

| Symptom                    | Cause                      | Resolution                                                                     |
| :------------------------- | :------------------------- | :----------------------------------------------------------------------------- |
| **Pipeline Failure (Red)** | Unexpected error           | Check GitHub Actions logs for specific `[ERROR]` tag.                          |
| **Missing Data**           | API failure/Non-market day | Normal if date is a holiday. Otherwise, trigger manual run.                    |
| **Unauthorized (401)**     | API Key expired/invalid    | Update Secrets in GitHub Repo Settings.                                        |
| **JSON Schema Error**      | Manual file corruption     | Validate files via `uv run scripts/python/jsonld_enricher.py --validate-only`. |

### Manual Recovery Procedure

If a step fails or is skipped erroneously:

1. Navigate to **Actions** → **Intraday Market Cycle**.
2. Click **"Run workflow"**.
3. Choose the specific step (`prediction`, `ato`, `atc`, `validation`) or `all`.
4. Monitor the logs for the specific `[ERROR]` or `[SKIP]` messages.

---

## 3. Dashboard Maintenance

The dashboard visualizes the `reports/metrics.json` artifact.

### Maintenance Tasks

- **Deployment**: The dashboard is statically hosted (GitHub Pages). Updating the `reports/` folder automatically triggers the dashboard update.
- **Refresh**: If metrics appear stale, check if the `Intraday Market Cycle` workflow successfully completed the `Validation & Metrics` step and committed to `main`.
- **Data Source**: If new regimes are added to the taxonomy, update `docs/010-regime-taxonomy-v01.json` and ensure the dashboard frontend is updated to recognize the new regimes.

---

## 4. System Governance

- **Stable Pipeline**: Changes to pipeline logic must be verified with `bash ./.tmp/run_tests.sh` (78 tests).
- **Secrets Management**: Never commit credentials. Use `.tmp/.env` for local testing and GitHub Secrets for CI/CD.
- **Naming Conventions**: All new documents MUST follow `NNN-kebab-case-vNN.ext`.

---

**Status**: Operational
**Governance**: Compliant with "Lean PSI Validator" principles.
