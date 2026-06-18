# Blueprint: PSI Performance Auditor (psi-performance-auditor)

**Status**: Draft
**Objective**: Automate performance monitoring of the PSI validation pipeline and trigger forensic RFCs upon threshold breaches.

## 1. Functional Scope

The `psi-performance-auditor` is an atomic monitor that evaluates `reports/metrics.json` after every execution cycle.

- **Threshold Monitoring**: Checks `overall_accuracy` and `rolling_7d`.
- **Breach Trigger**: If `overall_accuracy < 0.7` or `rolling_7d < 0.7`, it initiates a forensic audit.
- **Artifact Generation**: Automatically creates a `docs/02_rfc/YYYYMMDD-anomaly-report.md` containing:
  - Current metrics snapshot.
  - Confusion matrix analysis.
  - Suggested hypothesis adjustment.

## 2. Integration Logic

- **Trigger**: Called via `uv run` post-validation.
- **Input**: `reports/metrics.json` (JSON).
- **Execution**:
  1. Read `reports/metrics.json`.
  2. Compare against threshold constants.
  3. If breach: Call `init` (or equivalent RFC generator) to create the audit doc.
  4. Log status to `docs/00_todo_audit.md`.

## 3. Governance (Lean Constraints)

- **Zero Abstraction**: Must use existing `pandas` structures for metric comparison.
- **No External State**: Only relies on the `reports/` folder.
- **Determinism**: Thresholds are hardcoded in the auditor script; no "fuzzy" AI logic for the trigger itself.

## 4. Implementation Steps

1. Create `scripts/python/psi_auditor.py`.
2. Integrate into `scripts/sh/deploy.sh` (post-validation).
3. Validate trigger with a mock low-accuracy `metrics.json`.
