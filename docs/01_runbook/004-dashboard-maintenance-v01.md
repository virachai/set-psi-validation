# Runbook: Dashboard Maintenance (v01)

- **Purpose**: Procedures for maintaining and updating the PSI validation dashboard.
- **Applies to**: `dashboards/` directory and GitHub Pages
- **Last Updated**: 2026-06-14

---

## 1. Dashboard Overview

The dashboard is a static site hosted on GitHub Pages, consuming data from `reports/metrics.json`.

## 2. Maintenance Procedures

### 2.1. Updating Data Source

- The dashboard automatically updates whenever the `Intraday Market Cycle` workflow completes the `Validation & Metrics` step.
- No manual action is required unless the `metrics.json` structure changes.

### 2.2. Extending Regime Taxonomy

If the PSI Engine introduces new regimes (e.g., "Recovery"):

1. Update `docs/010-regime-taxonomy-v01.json` to include the new term.
2. Ensure the dashboard frontend (in `dashboards/`) has logic to map/display this new regime correctly.
3. Commit and push to `main` to trigger the deployment.

### 2.3. Dashboard Visuals

- To modify charts or visual aesthetics, edit the HTML/JS files in the `dashboards/` directory.
- Verify changes by hosting the dashboard locally (e.g., `python -m http.server` inside `dashboards/`) before pushing.

---

## 3. Data Flow Troubleshooting

If the dashboard appears stale:

1. **Check Reports**: Does `reports/metrics.json` contain the latest date?
2. **Workflow Success**: Did the last `Intraday Market Cycle` workflow complete successfully?
3. **GitHub Pages Status**: Check **Settings -> Pages** in the GitHub Repo to confirm the latest deployment was successful.

---

**Status**: Operational
**Governance**: Compliant with "Lean PSI Validator" principles.
