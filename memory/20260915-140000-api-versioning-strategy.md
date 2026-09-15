# Architecture Strategy: API Versioning and Longitudinal Validation

## 1. Overview
This document outlines the architectural strategy to evolve the SET PSI Validation pipeline into a robust platform for model research, A/B testing, and longitudinal analysis. The goal is to support multiple API versions (Challenger/Champion model) while preserving historical data integrity.

## 2. API Versioning Strategy
- **Versioning:** Transition to a multi-versioned fetching architecture.
- **Wrapper Layer:** Implement a centralized `fetch_psi.py` script that accepts a `version` argument.
- **Backward Compatibility:** Maintain the stable version (Champion) while deploying experimental versions (Challengers). Both must adhere to the standardized `docs/02_research_reports/005-prediction-snapshot-schema-v01.json` schema.

## 3. Data Storage & Archival
- **Immutable Storage:** Migrate from flat storage to a versioned hierarchy to ensure data integrity and auditability.
- **Storage Structure:**
  ```text
  data_archive/
  ├── v1/
  │   ├── 2026-09-09-am.json
  │   └── ...
  ├── v2/
  │   ├── 2026-09-09-am.json
  │   └── ...
  └── metadata.json  # Documents version diffs, model parameters, and thresholds.
  ```

## 4. Validation & Evaluation (A/B Testing)
- **Fan-out Validation:** The pipeline will execute validation against all active API versions simultaneously.
- **Challenger vs. Champion:** Compare model performance (Accuracy, F1 Score) daily.
- **Model Drift Detection:** Long-term tracking of performance metrics to identify when a specific model version degrades relative to market regimes.

## 5. Implementation Roadmap
1. **Refactor Fetcher:** Update `scripts/python/` to parameterize API versions.
2. **Update Pipeline:** Modify `intraday-pipeline.yml` to run validation fan-out.
3. **Longitudinal Reporting:** Develop tools to aggregate performance trends across all historical versions to support research decisions.
