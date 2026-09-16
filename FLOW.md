# SET PSI Validation: Intraday Execution & Truth Layer Flow

This document defines the end-to-end intraday execution cycle, data ingestion, and validation flow for the **SET PSI Validation** ecosystem using a Mermaid architecture diagram.

## 1. Intraday Execution & Validation Flowchart

```mermaid
graph TD
    subgraph "Pre-Market (09:00 ICT)"
        A[GitHub Actions Cron / Dispatch] -->|09:00 ICT| B[Fetch PSI Prediction API]
        B -->|Store Snapshot| C["predictions/{date}-{time}-am.json & full_day.json"]
    end

    subgraph "Intraday Session Windows (ICT Time)"
        D1["10:00 ICT: ATO Market Open"] -->|Capture ATO quote| E1["market-data/{date}-100000-ato.json"]
        D2["12:30 ICT: Noon Close"] -->|Capture Noon quote| E2["market-data/{date}-123000-noon.json"]
        D3["14:30 ICT: PM Open"] -->|Capture PM Open quote| E3["market-data/{date}-143000-pmopen.json"]
        D4["16:30 ICT: ATC Market Close"] -->|Capture ATC quote| E4["market-data/{date}-164500-atc.json"]
    end

    subgraph "Post-Market Validation (17:00 ICT)"
        E1 & E2 & E3 & E4 -->|Window Matching & Lookahead Guard| F[Validation Engine: validation_engine.py]
        C --> F
        F -->|Derive Actual Regime & Return| G["Compute Accuracy & F1 Score"]
        G -->|Save Evaluation Record| H["validation/{date}-{time}-{session}.json"]
        G -->|Aggregate Metrics| I["reports/metrics.json & reports/audit_report.json"]
    end

    subgraph "Visualization Layer"
        I -->|Read JSON Artifacts| J["SET PSI Dashboard (GitHub Pages / Static UI)"]
    end
```

---

## 2. Core Operational Rules

1. **No Lookahead Bias:** Prediction capture (Pre-ATO at 09:00) must occur strictly before market opening quotes (ATO at 10:00) are recorded.
2. **Four-Session Granularity:** The pipeline captures and validates across four intraday windows (ATO, Noon, PM Open, ATC) to evaluate regime consistency throughout the trading day.
3. **Deterministic Truth Layer:** Market outcomes are derived purely from verified price action and rolling volatility calculations, serving as an objective audit benchmark for PSI predictions.
