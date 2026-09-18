# SET PSI Validation: Intraday Execution & Truth Layer Flow

This document defines the end-to-end intraday execution cycle, data ingestion, and validation flow for the **SET PSI Validation** ecosystem using a Mermaid architecture diagram.

## 1. Intraday Execution & Validation Flowchart

```mermaid
graph TD
    subgraph "Pre-Market Retry Window (05:00-09:59 ICT)"
        A[GitHub Actions Cron / Dispatch] --> B[Fetch PSI Prediction API]
        B -->|Store Snapshot| C["predictions/{date}-{time}-full_day.json"]
    end

    subgraph "Post-Close Retry Window (16:45-23:59 ICT)"
        D["Fetch day's ATO + ATC in one call"] -->|capture_market.py --mode atc| E["market-data/{date}-{time}-atc.json"]
        E -->|Same workflow step| F[Validation Engine: validation_engine.py]
        C --> F
        F -->|Compare Predicted vs Actual Regime| G["Compute Accuracy & F1 Score"]
        G -->|Save Evaluation Record| H["validation/{date}-{time}-full_day.json"]
        G -->|Aggregate Metrics| I["reports/metrics.json & reports/audit_report.json"]
    end

    subgraph "Visualization Layer"
        I -->|Read JSON Artifacts| J["SET PSI Dashboard (GitHub Pages / Static UI)"]
    end
```

---

## 2. Core Operational Rules

1. **No Lookahead Bias:** Prediction capture must complete before the 10:00 ICT market open (ATO).
2. **Single Daily Cycle:** One `full_day` prediction, one post-close ATC capture (ATO and ATC fetched together), one validation per trading day (RFC 020). Retries are idempotent: a date with a complete ATC record is skipped.
3. **Deterministic Truth Layer:** Market outcomes are derived purely from verified price action and rolling volatility calculations, serving as an objective audit benchmark for PSI predictions.
