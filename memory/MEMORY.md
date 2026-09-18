---
name: memory-index
description: Index of project memory files
metadata:
    pinned: true
---

# Project Memory Index

- [Project Overview](20260614-120000-project-overview.md) - Initial project structure and status tracking.
- [Prediction Window Lower-Bound Gate](20260914-190000-prediction-window-lower-bound-gate.md) - Closed a gap where workflow_dispatch step=all could pass the lookahead-bias timestamp check for all three sessions at once.
- [PSI Design Complete](20260614-140000-psi-design-complete.md) - Architectural design phase finalized.
- [Schema.org Mapping Complete](20260614-150000-schema-org-mapping.md) - Schema.org type mapping for all PSI data artifacts.
- [Pipeline Implementation Complete](20260614-160000-pipeline-implementation.md) - RFC, scripts, workflows, tests, API integration with schema.org JSON-LD.
- [API Standardization Complete](20260614-170000-api-standardization-complete.md) - Lambda returns schema.org Observation, RapidAPI passthrough confirmed, tests updated.
- [SETSMART Integration Complete](20260614-180000-setsmart-integration.md) - capture_market.py fetches live SET Index ATO/ATC/volatility from SETSMART API.
- [Project Quality & CI Restored](20260614-190000-project-quality-and-ci-restored.md) - Fixed ruff CI failure, added pyproject.toml, improved market data resilience, and corrected test assertions.
- [Decoupled Prediction Capture](20260614-210000-decoupled-prediction-capture.md) - Architectural decision to store predictions independently of market data to improve data completeness.
- [Secure Local Test Runner](20260614-220000-secure-local-test-runner.md) - Secure local test runner using .tmp/.env and run_tests.sh.
- [Validation Engine & Dashboard Complete](20260614-190000-validation-engine-complete.md) - Phase 2 validation engine, Phase 3 dashboard, pyproject.toml, workflow fix.
- [Taxonomy Renamed & CI Green](20260614-200000-taxonomy-rename-ci-green.md) - Renamed to naming convention, all refs updated, API and CI verified passing.
- [2026-06-15 Market Cycle Execution Report](20260615-203000-market-cycle-report.md) - Automated market cycle execution report.
- [Memory: Community Standards Adoption](20260616-150000-community-standards-adoption.md) - Adoption of MIT license and community governance files.
- [Workflow Scheduling Fixed](20260616-193000-workflow-scheduling-fixed.md) - Fixed incorrect cron times and Lookahead Bias error handling.
- [Workflow Timezone & Observability](20260617-110000-workflow-timezone-observability.md) - Dual-zone ICT/UTC logic, enhanced logging, and execution safety guards.
- [Agents vs Claude Directory Audit](20260617-113900-agents-claude-audit.md) - Full audit of .agents/ and .claude/ duplicates. Decision: .agents/ is canonical shared location, .claude/ is Claude-specific config.
- [Cron Interval & Idempotent Scripts](20260617-200000-cron-interval-idempotent.md) - Changed cron to */30 with range-based time windows and idempotent scripts to tolerate GitHub Actions queue delay.
- [Crisis Regime Logic Fix](20260618-151000-crisis-regime-logic-fix.md) - Fixed boundary condition in Crisis regime derivation logic.
- [Enterprise Lean Gate](20260828-103000-enterprise-lean-gate.md) - Rejected Airflow/ELK/Vault per lean governance; adopted stubbed SETSMART integration tests + Mermaid docs.
- [Artifact Naming Convention](20260828-113000-artifact-naming-convention.md) - Unified {date}-{time}-{suffix}.json naming + ICT timestamps across data dirs.
- [Validation Engine Categorical Fix](20260829-140000-validation-engine-categorical-fix.md) - Resolved Pandas4Warning by adding Unclassified to VALID_REGIMES.
- [Husky Pre-commit Ordering](20260829-120000-husky-pre-commit-ordering.md) - Ordered ruff check before pytest in pre-commit hook
- [Finnhub Market Data Capture](20260902-140000-finnhub-market-data-capture.md) - Captured market data using Finnhub provider and verified JSON-LD enrichment.
- [Yahoo Finance Provider Integration](20260902-143000-yfinance-provider.md) - Configured yfinance as default provider for SET index capture.
- [Ruff ALL Lint Standard](20260902-163000-ruff-all-lint-standard.md) - select=ALL in pyproject; scripts/python has no __init__.py (mypy module collision); tuple-row dict fix in stress_test_regime.
- [Ruff Lint Fixes v2](20260902-183000-ruff-lint-fixes-v2.md) - Resolved CPY001 and PLR0917 lint errors in CI.
- [Enterprise Husky Pre-Commit](20260902-190000-enterprise-husky-pre-commit.md) - Upgraded pre-commit hook to LV99 enterprise-grade validation.
- [Regime Scoring & Adaptive Threshold Fix](20260903-210000-regime-scoring-and-adaptive-threshold-fix.md) - Fixed Unclassified-counted-as-correct bug and replaced hardcoded volatility threshold with real 30-day rolling computation.
- [20260903-120000-psi-validation-remediation-rfc.md](20260903-120000-psi-validation-remediation-rfc.md): RFC-001 creation for PSI validation pipeline findings remediation.
- [Finnhub vs yfinance for Thai Stock EOD Validation POC](20260908-103000-finnhub-vs-yfinance-thai-stock-poc.md) - Empirical POC testing Finnhub vs yfinance on Thai stocks; Finnhub locked behind 403 on free tier, yfinance verified viable for batch EOD validation.
- [Gauntlet Loop Enterprise Runbook](20260908-120000-gauntlet-loop-enterprise-runbook.md) - Level 99 enterprise-grade SOP and FMEA framework for Gauntlet Loop executions.
- [PSI Validation Flow Frozen](20260908-140000-psi-validation-flow-frozen.md) - Confirmation of pipeline flow integrity and scope freeze for long-term execution.
- [API Versioning Strategy](20260915-140000-api-versioning-strategy.md) - Architectural strategy for versioning PSI APIs and evolving the validation pipeline to handle multi-version evaluation, ensuring backward compatibility and long-term data archival.
- [Capture Window Enforcement](20260915-193000-capture-window-enforcement.md) - The single atc capture is guarded by CAPTURE_WINDOWS (>= 16:30 ICT); backfills and bypassed captures must carry a provenance stamp.
- RFC 020 (`docs/02_rfc/020-rfc-lean-single-cycle-rollback-v01.md`) - Single daily cycle: one full_day prediction, one post-close ATC capture, one validation. RFC 016/017 and their multi-session memory entries were deleted.
