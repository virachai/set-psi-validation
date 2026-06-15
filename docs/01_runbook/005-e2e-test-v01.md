# Runbook: E2E Smoke Test (v01)

- **Purpose**: Verify the full PSI validation pipeline end-to-end — prediction fetch, market data extraction, validation engine, and output verification.
- **Applies to**: `set-psi-validation` pipeline
- **Last Updated**: 2026-06-15

---

## 1. Quick Start

```bash
# Default: full_day session, today's date
bash scripts/sh/e2e_test.sh

# Specific session and date
bash scripts/sh/e2e_test.sh 2026-06-15 am
bash scripts/sh/e2e_test.sh 2026-06-15 pm
bash scripts/sh/e2e_test.sh 2026-06-15 full_day
```

The e2e test is also included as step 5/5 in `run_tests.sh all` and `test.sh all`.

## 2. Test Flow

| Step | Script                            | What It Checks                                                        |
| ---- | --------------------------------- | --------------------------------------------------------------------- |
| 1    | `predictions_loader.py --session` | Fetches PSI prediction from API; skips cleanly if outside time window |
| 2    | `extract_pdf.py --date`           | Extracts market data from PDF source                                  |
| 3    | `validation_engine.py --date`     | Runs regime comparison, generates validation records                  |
| 4    | Output check                      | Verifies `predictions/`, `validation/`, `reports/` have JSON files    |

## 3. Expected Results

### Normal Run (within session window)

```text
[OK] predictions/ has N file(s)
[OK] validation/ has N file(s)
[OK] reports/ has 1 file(s)
[DONE] E2E smoke test passed.
```

### Out-of-Window Run (e.g. AM at 14:00 ICT)

```text
[SKIP] Prediction capture skipped — outside am window.
...
[OK] predictions/ has N file(s)
[DONE] E2E smoke test passed.
```

The pipeline is resilient — it uses existing prediction snapshots if the current fetch is outside the valid window. The test still passes as long as historical output files exist.

## 4. Failure Modes

| Symptom                               | Likely Cause                            | Action                                              |
| ------------------------------------- | --------------------------------------- | --------------------------------------------------- |
| `API Authentication failed (401/403)` | `PSI_ENGINE_API_KEY` missing or invalid | Check secrets in `.env` or GitHub Actions           |
| No prediction files found             | First run with no historical data       | Ensure API key is set and run within session window |
| Validation step produces no records   | No market data for the date             | Check `market-data/` directory for the date file    |
| Test exits with error                 | One of the scripts crashed              | Re-run that step individually to isolate the issue  |

## 5. Integration

The e2e test is invoked automatically when running:

```bash
# Full pipeline check (ruff + black + mypy + pytest + e2e)
bash scripts/sh/run_tests.sh all
bash scripts/sh/test.sh all
```

---

**Status**: Operational
**Governance**: Compliant with "Lean PSI Validator" principles.
