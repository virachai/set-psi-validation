# SET PSI Validation: Master Project Index

Welcome to the **SET PSI Validation** repository. This document serves as the master navigation index for the repository, connecting core architecture, operational runbooks, research reports, RFCs, and historical memory logs.

---

## 1. Core Architecture & Philosophy

- **[GEMINI.md](GEMINI.md)**: Foundational project instructions, engineering standards, and operational workflows.
- **[CLAUDE.md](CLAUDE.md)**: AI collaboration guidelines and workspace conventions.
- **[FLOW.md](FLOW.md)**: Intraday execution cycle and validation truth layer architecture diagram.
- **[ROADMAP.md](docs/ROADMAP.md)**: Ecosystem roadmap and milestone tracker.

---

## 2. Runbooks & Operational Guides (`docs/01_runbook/`)

- **[GitHub Setup Runbook](docs/01_runbook/001-github-setup-v01.md)**: Initial CI/CD and repository setup.
- **[PSI Validator Runbook](docs/01_runbook/001-psi-validator-runbook-v01.md)**: Step-by-step validator execution guide.
- **[Operations & Maintenance](docs/01_runbook/002-operations-maintenance-v01.md)**: Routine maintenance procedures.
- **[Troubleshooting Guide](docs/01_runbook/003-troubleshooting-guide-v01.md)**: Common failure modes and resolutions.
- **[Dashboard Maintenance](docs/01_runbook/004-dashboard-maintenance-v01.md)**: Maintaining the visualization layer.
- **[E2E Test Runbook](docs/01_runbook/005-e2e-test-v01.md)**: End-to-end testing procedures.
- **[Workflow Timezone Debug](docs/01_runbook/006-workflow-timezone-observability-v01.md)**: ICT/UTC synchronization and logging.
- **[Pipeline Anomaly Log](docs/01_runbook/007-pipeline-anomaly-log-v01.md)**: Historical execution anomaly tracking.
- **[Project Summary](docs/01_runbook/007-project-summary-v01.md)**: Comprehensive architectural summary.
- **[Gauntlet Loop Runbook](docs/01_runbook/008-gauntlet-loop-runbook-v01.md)**: Enterprise-grade FMEA and Gauntlet execution SOP.

---

## 3. Research Reports & Schemas (`docs/02_research_reports/`)

- **[Actual Regime Derivation Logic](docs/02_research_reports/001-actual-regime-derivation-logic-v01.md)**: Mathematical derivation of market regimes.
- **[Dashboard Requirements](docs/02_research_reports/002-dashboard-requirements-v01.md)**: Visualization specifications.
- **[Data Ingestion Plan](docs/02_research_reports/003-data-ingestion-plan-v01.md)**: Market data provider strategies (SETSMART / yfinance).
- **[Market Outcome Schema](docs/02_research_reports/004-market-outcome-schema-v01.json)**: JSON schema for market results.
- **[Prediction Snapshot Schema](docs/02_research_reports/005-prediction-snapshot-schema-v01.json)**: JSON schema for PSI predictions.
- **[Validation Evaluation Schema](docs/02_research_reports/006-validation-evaluation-schema-v01.json)**: Metrics output structure.
- **[Schema.org Mapping](docs/02_research_reports/008-schema-org-mapping-v01.md)**: Structured data mapping for financial observations.
- **[Lean Architecture & Data Truth Gap Analysis](docs/02_research_reports/009-lean-architecture-and-data-truth-gap-analysis-v01.md)**: Architectural gap analysis.
- **[Market Regime Analysis & Thresholds](docs/02_research_reports/010-market-regime-analysis-and-psi-thresholds-v01.md)**: Threshold tuning and volatility calculations.

---

## 4. Requests for Comments (`docs/02_rfc/`)

- **[RFC-001 Validation Remediation](docs/02_rfc/001-rfc-psi-validation-remediation-v01.md)**
- **[RFC-002 Modular Intraday Pipeline](docs/02_rfc/002-rfc-modular-intraday-pipeline-v01.md)**
- **[RFC-016 Four-Session Market Data Timing](docs/02_rfc/016-rfc-four-session-market-data-timing-v01.md)**
- **[RFC-017 Session-Aware Validation Alignment](docs/02_rfc/017-rfc-session-aware-validation-alignment-v01.md)**
- **[API Versioning Strategy](memory/20260915-140000-api-versioning-strategy.md)**: Multi-version architecture and longitudinal validation strategy.

---

## 5. Project Memory & Evolution (`memory/`)

- **[Project Memory Index](memory/MEMORY.md)**: Index of all architectural decision logs and chronological milestone reports.
- **[API Versioning Strategy Memory](memory/20260915-140000-api-versioning-strategy.md)**: Blueprint for Challenger/Champion model testing and versioned dataset archival.

---

## 6. Dashboards & Validation Artifacts

- **[Dashboards](dashboards/)**: Lightweight web visualization UI (`index.html`, `app.js`, `style.css`).
- **[Predictions](predictions/)**: Stored prediction snapshots.
- **[Market Data](market-data/)**: Historical ATO/ATC and intraday snapshots.
- **[Validation](validation/)**: Evaluation outputs and confusion matrix metrics.
