# RFC-002: Modular Intraday Pipeline Refactoring v01

## 1. Executive Summary

The current monolithic GitHub Action (`intraday-pipeline.yml`) manages all intraday market cycles in a single job. This creates a single point of failure, complicates observability, and increases the risk of Action queue delays impacting distinct market events (e.g., ATC capture). We propose decomposing this into modular, time-triggered workflows.

## 2. Motivation

- **Resilience:** Failure in one stage (e.g., AM prediction) does not block or complicate subsequent stages (e.g., ATC capture).
- **Observability:** Distinct job logs per market event improve debugging.
- **Maintainability:** Smaller, focused YAML files are easier to manage and version.
- **Scheduling:** Allows precise cron scheduling for each market event, reducing the "wide window" cron approach.

## 3. Proposed Structure

We will migrate the monolithic file to `docs/002-rfc-modular-intraday-pipeline-v01.md` and create individual workflows in `.github/workflows/`:

| Workflow File                | Trigger Time (ICT) | Responsibility          |
| :--------------------------- | :----------------- | :---------------------- |
| `market-prediction-am.yml`   | 08:00              | PSI AM Prediction       |
| `market-prediction-full.yml` | 09:00              | PSI Full Day Prediction |
| `market-capture-ato.yml`     | 10:00              | ATO Market Capture      |
| `market-capture-noon.yml`    | 12:30              | Noon Market Capture     |
| `market-prediction-pm.yml`   | 13:00              | PSI PM Prediction       |
| `market-capture-pmopen.yml`  | 14:30              | PM Open Market Capture  |
| `market-capture-atc.yml`     | 16:30              | ATC Market Capture      |
| `market-validation.yml`      | 17:00              | Validation & Metrics    |

## 4. Implementation Details

- **Shared Logic:** Extract shared environment variables and setup steps into a composite action or reusable workflow template to minimize duplication.
- **Data Integrity:** Maintain the existing `git` commit strategy but scope it to the specific workflow result.
- **Migration Path:**
  1. Create the new workflow files.
  2. Test each workflow individually via `workflow_dispatch`.
  3. Disable the monolithic `intraday-pipeline.yml`.
  4. Remove the legacy file after a successful 48-hour soak period.

## 5. Constraints

- Must remain compliant with Python `uv` standards.
- Must continue to respect market hours and avoid lookahead bias.
- No changes to the core Python logic in `scripts/python/`.

---

**Status**: Pending Approval
**Effective Date**: 2026-09-05
