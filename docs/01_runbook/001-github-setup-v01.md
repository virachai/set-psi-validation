# Runbook: GitHub Setup for PSI Validation Pipeline (v01)

- **Purpose**: Configure GitHub repository, secrets, and workflows for the automated intraday validation cycle.
- **Applies to**: `set-psi-validation` repository
- **Last Updated**: 2026-06-14

---

## 1. Prerequisites

| Item                                              | Check |
| :------------------------------------------------ | :---- |
| GitHub repository created and cloned locally      | ✓ / ✗ |
| Repository has `main` branch set as default       | ✓ / ✗ |
| Workflow files present in `.github/workflows/`    | ✓ / ✗ |
| All Python scripts in `scripts/python/` committed | ✓ / ✗ |
| `.env.example` committed (no secrets in it)       | ✓ / ✗ |

---

## 2. Required GitHub Secrets

The pipeline requires **6 secrets** to run the full intraday cycle. Set these in:

> **GitHub UI → Settings → Secrets and variables → Actions → Repository secrets**

| Secret               | Used By                        | Description                                     | Required |
| :------------------- | :----------------------------- | :---------------------------------------------- | :------- |
| `PSI_ENGINE_API_KEY` | `predictions_loader.py`        | API key for PSI Engine (prediction generation). | **Yes**  |
| `PSI_API_URL`        | `predictions_loader.py`        | Full URL to PSI Engine prediction endpoint.     | **Yes**  |
| `SET_MARKET_API_KEY` | `capture_market.py`            | API key for SET market data source.             | **Yes**  |
| `SET_ATO_PRICE`      | `capture_market.py` (ATO step) | ATO price for market open.                      | Yes\*    |
| `SET_ATC_PRICE`      | `capture_market.py` (ATC step) | ATC price for market close.                     | Yes\*    |
| `SET_VOLATILITY`     | `capture_market.py` (ATC step) | Intraday volatility index.                      | Yes\*    |

> _\* These have fallback defaults (`0`, `0.01`) in the workflow if not set, but should be configured with real data for production._

### Setting Secrets via CLI

```bash
# Install GitHub CLI first: https://cli.github.com/
gh secret set PSI_ENGINE_API_KEY --repo owner/set-psi-validation
gh secret set PSI_API_URL --repo owner/set-psi-validation
gh secret set SET_MARKET_API_KEY --repo owner/set-psi-validation
gh secret set SET_ATO_PRICE --repo owner/set-psi-validation
gh secret set SET_ATC_PRICE --repo owner/set-psi-validation
gh secret set SET_VOLATILITY --repo owner/set-psi-validation
```

You will be prompted to paste each value.

### Setting Secrets via UI

1. Navigate to `https://github.com/owner/set-psi-validation/settings/secrets/actions`
2. Click **"New repository secret"**
3. Add each secret from the table above
4. Verify secrets appear in the list after saving

---

## 3. Workflow Overview

### File: `.github/workflows/intraday-pipeline.yml`

**4 Scheduled Triggers (SET Market Hours — ICT timezone):**

| Cron (UTC)     | Local ICT | Step                 | Script                         |
| :------------- | :-------- | :------------------- | :----------------------------- |
| `0 2 * * 1-5`  | 09:00     | Prediction Capture   | `predictions_loader.py`        |
| `0 3 * * 1-5`  | 10:00     | ATO Capture          | `capture_market.py --mode ato` |
| `30 9 * * 1-5` | 16:30     | ATC Capture          | `capture_market.py --mode atc` |
| `0 10 * * 1-5` | 17:00     | Validation & Metrics | `validation_engine.py`         |

**Post-processing (runs after each step):**

- `jsonld_enricher.py` — injects schema.org `@context`/`@type` into all JSON files
- `git commit + push` — commits data back to the repository

### Manual Trigger

1. Go to `https://github.com/owner/set-psi-validation/actions`
2. Select **"Intraday Market Cycle"** from the left sidebar
3. Click **"Run workflow"** → select step:
   - `prediction` — run only prediction capture
   - `ato` — run only ATO capture
   - `atc` — run only ATC capture
   - `validation` — run only validation & metrics
   - `all` — run all steps sequentially

---

## 4. File Structure After Setup

After the workflow runs, the repository will contain:

```
set-psi-validation/
├── .github/workflows/intraday-pipeline.yml   # CI pipeline
├── catalog.json                                # DataCatalog (schema.org)
├── docs/
│   ├── regime-taxonomy.jsonld                  # DefinedTermSet (schema.org)
│   └── 01_runbook/001-github-setup-v01.md     # this file
├── predictions/
│   └── 2026-06-14.json                         # Prediction Observation
├── market-data/
│   └── 2026-06-14.json                         # Market Outcome Observation
├── validation/
│   └── 2026-06-14.json                         # Validation Evaluation Observation
├── reports/
│   └── aggregated-metrics.json                 # Dataset with metrics
└── scripts/python/
    ├── predictions_loader.py                   # PSI Engine API caller
    ├── capture_market.py                       # ATO/ATC data capture
    ├── validation_engine.py                    # Regime comparison logic
    └── jsonld_enricher.py                      # Schema.org enrichment
```

---

## 5. Verification Steps

Run these checks after setup to confirm the pipeline works.

### 5.1 Local Script Test

```bash
# Test prediction loader (dry run without API)
uv run scripts/python/predictions_loader.py
# Expected: error about missing API key (confirms script loads)

# Test market capture syntax
uv run scripts/python/capture_market.py --mode ato --ato-price 1450.20
# Expected: creates market-data/YYYY-MM-DD.json with ATO only

uv run scripts/python/capture_market.py --mode atc --atc-price 1438.10 --volatility 1.95
# Expected: updates market-data/YYYY-MM-DD.json with complete data

# Test validation engine
uv run scripts/python/validation_engine.py
# Expected: runs regime comparison, prints result

# Test JSON-LD enrichment
uv run scripts/python/jsonld_enricher.py --validate-only
# Expected: confirms all files have @context/@type
```

### 5.2 Workflow Test (Manual Trigger)

1. Push all committed files to `main`
2. Go to **Actions** tab → **Intraday Market Cycle**
3. Click **"Run workflow"** → select step `all`
4. Watch the workflow run in real-time
5. Verify the commit appears in the repository after success

### 5.3 Schema.org Validation

```bash
# Validate JSON-LD output files
uv run scripts/python/jsonld_enricher.py --validate-only
```

Alternatively, upload any output JSON file to:

- https://json-ld.org/playground/ — validates JSON-LD syntax
- https://search.google.com/test/rich-results — validates schema.org conformance

---

## 6. Troubleshooting

| Symptom                       | Likely Cause             | Fix                                                                    |
| :---------------------------- | :----------------------- | :--------------------------------------------------------------------- |
| Workflow shows ❌ but no logs | Missing GitHub secrets   | Go to Settings → Secrets and add missing values.                       |
| `uv sync` fails               | No `pyproject.toml`      | Create minimal `pyproject.toml` or use PEP 723 inline dependencies.    |
| Script not found              | `scripts/` not committed | Verify `.gitignore` allows `scripts/python/` (not `scripts/`).         |
| Empty commit                  | No data files changed    | CI ran but market data was unchanged. Normal for non-market days.      |
| Rich Results Test error       | `@context` wrong         | Check that `@context` is exactly `"https://schema.org"` (with `s`).    |
| Push rejected                 | Branch protection rules  | Disable "Require pull request" for `github-actions[bot]` or use a PAT. |

### Push Rejected — Branch Protection

If the `main` branch has branch protection rules:

**Option A — Allow bot directly:**

1. Settings → Branches → Edit protection rule
2. Add `github-actions[bot]` to **"Allow bypass"** list

**Option B — Use Personal Access Token:**

1. Create a PAT at `https://github.com/settings/tokens` (with `contents:write` scope)
2. Add as secret: `GH_PAT`
3. Update workflow commit step:
   ```yaml
   - name: Commit and Push changes
     run: |
       git remote set-url origin https://x-access-token:${{ secrets.GH_PAT }}@github.com/owner/set-psi-validation.git
       git add ...
       git commit -m "..."
       git push
   ```

---

## 7. Environment Variables Reference

| Variable                | Scope                 | Source                  | Required |
| :---------------------- | :-------------------- | :---------------------- | :------- |
| `PSI_API_URL`           | Local + GitHub secret | `.env` + GitHub Secrets | Yes      |
| `PSI_ENGINE_API_KEY`    | Local + GitHub secret | `.env` + GitHub Secrets | Yes      |
| `SET_MARKET_API_KEY`    | Local + GitHub secret | `.env` + GitHub Secrets | Yes      |
| `SET_ATO_PRICE`         | GitHub secret only    | External market feed    | Yes      |
| `SET_ATC_PRICE`         | GitHub secret only    | External market feed    | Yes      |
| `SET_VOLATILITY`        | GitHub secret only    | External market feed    | Yes      |
| `SUPABASE_DATABASE_URL` | Local only (optional) | `.env`                  | No       |

> **Security**: Never commit `.env` to the repository. Only `.env.example` with placeholder values should be committed.

---

**Status**: Operational
**Governance**: Compliant with "Lean PSI Validator" principles.
