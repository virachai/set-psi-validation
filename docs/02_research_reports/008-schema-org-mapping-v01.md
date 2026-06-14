# Schema.org Mapping for PSI Validation Pipeline (v01)

## Objective

Define a formal mapping between the PSI Validation data model and [schema.org](https://schema.org) types, enabling semantic interoperability and structured data compliance.

## Why Schema.org?

| Benefit | Description |
| :------ | :---------- |
| **Standardization** | Aligns the PSI ecosystem with W3C-recognized vocabulary for structured data on the web. |
| **Discoverability** | Datasets annotated with schema.org can be discovered by search engines and data catalogs (Google Dataset Search). |
| **Interchange** | Reduces friction when exchanging data with external systems (dashboard, PSI Engine, research partners). |
| **Self-Documenting** | Each data artifact carries its own semantic context, reducing reliance on external docs. |

---

## 1. Core Type Mapping

| PSI Component | Schema.org Type | Rationale |
| :------------ | :-------------- | :-------- |
| **Regime Taxonomy** (Bullish/Bearish/etc.) | `DefinedTermSet` + `DefinedTerm` | Formal controlled vocabulary for the 5 market regimes. |
| **Prediction Snapshot** (Pre-ATO) | `Observation` | A prediction is an observation of a forecast at a point in time. `observationDate` captures the pre-ATO timestamp. |
| **Market Outcome** (ATO/ATC) | `Observation` | Market behavior is observed intraday. `variableMeasured` captures prices, return, and volatility. |
| **Validation Evaluation** (Prediction vs Outcome) | `Observation` + `marginOfError` | The comparison result is an observation of accuracy. `marginOfError` maps directly to `deviationScore`. |
| **PSI Score** | `PropertyValue` | Key-value pair with min/max bounds. |
| **ATO/ATC Price** | `QuantitativeValue` | SET Index points — a numerical quantity, not a monetary value directly. |
| **All Data Collections** | `Dataset` | Each directory (`predictions/`, `market-data/`, `validation/`) is a dataset. |
| **Whole System** | `DataCatalog` | Top-level container organizing all datasets. |
| **Accuracy Metrics** | `AggregateRating` | Overall accuracy maps to `ratingValue`/`bestRating`. |
| **Per-Regime Metrics** | `PropertyValue` | Precision, Recall, F1 per regime. |
| **PSI Engine API** | `EntryPoint` | External API contract for the prediction source. |

---

## 2. Detailed Mapping per Artifact

### 2.1 Regime Taxonomy — `DefinedTermSet` + `DefinedTerm`

```json
{
  "@context": "https://schema.org",
  "@type": "DefinedTermSet",
  "name": "PSI Market Regime Classification",
  "description": "Taxonomy of market regime labels used by the PSI (Pressure-Signal Index) system for the SET (Stock Exchange of Thailand) market.",
  "url": "https://github.com/user/set-psi-validation/docs/regime-taxonomy",
  "hasDefinedTerm": [
    {
      "@type": "DefinedTerm",
      "name": "Bullish",
      "termCode": "BULLISH",
      "description": "Strong positive intraday return with broad-based market strength."
    },
    {
      "@type": "DefinedTerm",
      "name": "Bearish",
      "termCode": "BEARISH",
      "description": "Consistent intraday decline with weak closing relative to ATO."
    },
    {
      "@type": "DefinedTerm",
      "name": "Sideways",
      "termCode": "SIDEWAYS",
      "description": "Low directional movement in a range-bound trading session."
    },
    {
      "@type": "DefinedTerm",
      "name": "Risk-Off",
      "termCode": "RISK_OFF",
      "description": "Defensive behavior with increased volatility and negative bias."
    },
    {
      "@type": "DefinedTerm",
      "name": "Crisis",
      "termCode": "CRISIS",
      "description": "Sharp downside move with extreme volatility spike."
    }
  ]
}
```

**Properties used:**

| Schema.org Property | Usage |
| :------------------ | :---- |
| `hasDefinedTerm` | Array of regime terms in the set. |
| `termCode` | Machine-readable identifier (e.g., `BULLISH`). |
| `name` | Human-readable label. |
| `description` | Definition of the regime conditions. |

---

### 2.2 Prediction Snapshot — `Observation`

**Field Mapping:**

| Existing Field | Schema.org Path | Notes |
| :------------- | :-------------- | :---- |
| `date` | `observationDate` | Trading date of the prediction. |
| `timestamp` | `observationDate` (time component) | Pre-ATO time (~09:00 ICT). |
| `predictedRegime` | `measuredProperty` → `DefinedTerm` | The property being measured is "which regime will occur." |
| `psi.score` | `variableMeasured` → `PropertyValue` | Numeric score with [0, 1] range. |
| `modelId` | `measurementMethod` | Identifies the prediction method/model version. |

**JSON-LD Example:**

```json
{
  "@context": "https://schema.org",
  "@type": "Observation",
  "name": "PSI Prediction 2026-06-14",
  "observationDate": "2026-06-14T09:00:00+07:00",
  "measuredProperty": {
    "@type": "DefinedTerm",
    "name": "Predicted Regime",
    "inDefinedTermSet": "psi:market-regimes"
  },
  "variableMeasured": [
    {
      "@type": "PropertyValue",
      "name": "PSI Score",
      "value": 0.41,
      "minValue": 0,
      "maxValue": 1
    },
    {
      "@type": "PropertyValue",
      "name": "Predicted Regime",
      "value": "RISK_OFF"
    }
  ],
  "measurementMethod": {
    "@type": "DefinedTerm",
    "name": "PSI Engine v1"
  }
}
```

---

### 2.3 Market Outcome — `Observation`

**Field Mapping:**

| Existing Field | Schema.org Path | Notes |
| :------------- | :-------------- | :---- |
| `date` | `observationDate` | Trading date. |
| `ato` | `variableMeasured` → `QuantitativeValue` | Opening index level. |
| `atc` | `variableMeasured` → `QuantitativeValue` | Closing index level. |
| `returnPct` | `variableMeasured` → `PropertyValue` | Intraday return as percentage. |
| `volatilityIndex` | `variableMeasured` → `PropertyValue` | Intraday volatility proxy. |
| `actualRegime` | `measuredProperty` → `DefinedTerm` | Ground truth regime derived post-market. |

**JSON-LD Example:**

```json
{
  "@context": "https://schema.org",
  "@type": "Observation",
  "name": "SET Market Outcome 2026-06-14",
  "observationDate": "2026-06-14",
  "observationPeriod": "2026-06-14T10:00:00+07:00/2026-06-14T16:30:00+07:00",
  "measuredProperty": {
    "@type": "DefinedTerm",
    "name": "Actual Regime",
    "inDefinedTermSet": "psi:market-regimes"
  },
  "variableMeasured": [
    {
      "@type": "QuantitativeValue",
      "name": "ATO Price",
      "value": 1450.20,
      "unitText": "SET Index Points"
    },
    {
      "@type": "QuantitativeValue",
      "name": "ATC Price",
      "value": 1438.10,
      "unitText": "SET Index Points"
    },
    {
      "@type": "PropertyValue",
      "name": "Return %",
      "value": -0.83
    },
    {
      "@type": "PropertyValue",
      "name": "Intraday Volatility",
      "value": 1.95
    },
    {
      "@type": "PropertyValue",
      "name": "Actual Regime",
      "value": "RISK_OFF"
    }
  ]
}
```

---

### 2.4 Validation Evaluation — `Observation` + `marginOfError`

**Field Mapping:**

| Existing Field | Schema.org Path | Notes |
| :------------- | :-------------- | :---- |
| `date` | `observationDate` | Validation date. |
| `predictionId` | `observationAbout` (target 1) | Links to the prediction `Observation`. |
| `outcomeId` | `observationAbout` (target 2) | Links to the outcome `Observation`. |
| `isCorrect` | `variableMeasured` → `PropertyValue` | Boolean accuracy flag. |
| `deviationScore` | `marginOfError` → `QuantitativeValue` | **Direct 1:1 mapping.** |

**JSON-LD Example:**

```json
{
  "@context": "https://schema.org",
  "@type": "Observation",
  "name": "Validation Evaluation 2026-06-14",
  "observationDate": "2026-06-14T17:00:00+07:00",
  "observationAbout": [
    {"@id": "predictions/2026-06-14.json"},
    {"@id": "market-data/2026-06-14.json"}
  ],
  "measuredProperty": {
    "@type": "DefinedTerm",
    "name": "Regime Prediction Accuracy",
    "inDefinedTermSet": "psi:market-regimes"
  },
  "variableMeasured": {
    "@type": "PropertyValue",
    "name": "Is Correct",
    "value": true
  },
  "marginOfError": {
    "@type": "QuantitativeValue",
    "value": 0.0,
    "description": "Deviation score: 0 = perfect match, higher = greater misalignment."
  }
}
```

**Why `marginOfError` is the key match:** schema.org defines `marginOfError` as "quantitative value indicating the magnitude of error in an Observation." The PSI system's `deviationScore` captures exactly this — how far off the prediction was from reality.

---

### 2.5 Aggregated Metrics — `Dataset` + `AggregateRating`

**Accuracy as `AggregateRating`:**

```json
{
  "@context": "https://schema.org",
  "@type": "AggregateRating",
  "name": "PSI Overall Accuracy",
  "description": "Rolling accuracy of PSI regime predictions.",
  "ratingValue": 82.5,
  "bestRating": 100,
  "worstRating": 0,
  "ratingCount": 35
}
```

**Per-Regime Metrics as `PropertyValue` Array:**

```json
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "PSI Aggregated Metrics",
  "description": "Rolling classification metrics for the PSI validation pipeline.",
  "variableMeasured": [
    {
      "@type": "PropertyValue",
      "name": "Accuracy",
      "value": 0.825
    },
    {
      "@type": "PropertyValue",
      "name": "Precision (Bullish)",
      "value": 0.78
    },
    {
      "@type": "PropertyValue",
      "name": "Recall (Bullish)",
      "value": 0.72
    },
    {
      "@type": "PropertyValue",
      "name": "F1 Score",
      "value": 0.75
    }
  ],
  "measurementTechnique": "Confusion matrix analysis on rolling 30-day window."
}
```

---

### 2.6 PSI Score — `StatisticalVariable`

```json
{
  "@context": "https://schema.org",
  "@type": "StatisticalVariable",
  "name": "PSI Score (Pressure-Signal Index)",
  "description": "A normalized score [0, 1] representing the predicted pressure-signal intensity for the current trading session.",
  "measuredProperty": "psiScore",
  "populationType": "SET TradingDays",
  "statType": "https://schema.org/PropertyValue",
  "measurementMethod": "PSI Engine v1"
}
```

---

### 2.7 Data Catalog — `DataCatalog`

```json
{
  "@context": "https://schema.org",
  "@type": "DataCatalog",
  "name": "SET PSI Validation Data Catalog",
  "description": "Complete catalog of all data artifacts in the PSI (Pressure-Signal Index) validation pipeline for the Stock Exchange of Thailand.",
  "dataset": [
    {
      "@type": "Dataset",
      "name": "PSI Predictions",
      "description": "Pre-ATO regime forecast snapshots.",
      "url": "https://github.com/user/set-psi-validation/tree/main/predictions"
    },
    {
      "@type": "Dataset",
      "name": "Market Outcomes",
      "description": "Observed ATO/ATC intraday market data.",
      "url": "https://github.com/user/set-psi-validation/tree/main/market-data"
    },
    {
      "@type": "Dataset",
      "name": "Validation Evaluations",
      "description": "Prediction vs outcome comparison records.",
      "url": "https://github.com/user/set-psi-validation/tree/main/validation"
    },
    {
      "@type": "Dataset",
      "name": "Aggregated Metrics",
      "description": "Rolling accuracy, F1, precision, recall, and confusion matrix.",
      "url": "https://github.com/user/set-psi-validation/tree/main/reports"
    }
  ],
  "measurementTechnique": "PSI Validation Protocol v1 — compare predicted regime against derived actual regime using deterministic classification rules."
}
```

---

## 3. Visual Relationship Diagram

```text
DataCatalog  "SET PSI Validation"
 │
 ├── DefinedTermSet  "Market Regime Taxonomy"
 │    ├── DefinedTerm  "Bullish"
 │    ├── DefinedTerm  "Bearish"
 │    ├── DefinedTerm  "Sideways"
 │    ├── DefinedTerm  "Risk-Off"
 │    └── DefinedTerm  "Crisis"
 │
 ├── Dataset  "PSI Predictions"
 │    └── Observation  (per-day prediction)
 │         ├── observationDate    → pre-ATO timestamp
 │         ├── measuredProperty  → DefinedTerm (predicted regime)
 │         ├── variableMeasured  → PropertyValue (PSI score)
 │         └── measurementMethod → PSI Engine version
 │
 ├── Dataset  "Market Outcomes"
 │    └── Observation  (per-day outcome)
 │         ├── observationDate    → trading date
 │         ├── measuredProperty  → DefinedTerm (actual regime)
 │         └── variableMeasured  → QuantitativeValue[] (ATO, ATC, return, volatility)
 │
 ├── Dataset  "Validation Evaluations"
 │    └── Observation  (per-day validation)
 │         ├── observationDate    → validation timestamp
 │         ├── observationAbout  → [prediction, outcome] (links)
 │         ├── variableMeasured  → PropertyValue (isCorrect)
 │         └── marginOfError     → QuantitativeValue (deviationScore)
 │
 └── Dataset  "Aggregated Metrics"
      ├── AggregateRating  → overall accuracy
      └── PropertyValue[]  → F1, precision, recall per regime
```

---

## 4. Integration with Existing Schemas

The three existing JSON Schemas (004-market-outcome, 005-prediction-snapshot, 006-validation-evaluation) are compatible with this mapping. Each schema file now includes:

| File | `@type` (schema.org) | Key Mapping |
| :--- | :------------------- | :---------- |
| `004-market-outcome-schema-v01.json` | `Observation` | `variableMeasured` contains ATO, ATC, return, volatility |
| `005-prediction-snapshot-schema-v01.json` | `Observation` | `measurementMethod` = modelId, `variableMeasured` = psi score |
| `006-validation-evaluation-schema-v01.json` | `Observation` | `observationAbout` links prediction + outcome, `marginOfError` = deviationScore |

---

## 5. Limitations & Notes

- **No Financial Market Type in Schema.org**: Schema.org lacks a dedicated "MarketRegimePrediction" or "FinancialForecast" type. `Observation` is the closest semantic fit and is intentionally generic.
- **Price vs Index Level**: SET Index values (ATO/ATC) are index points, not currency amounts. `QuantitativeValue` is preferred over `MonetaryAmount` for accuracy.
- **Deviation as marginOfError**: The `marginOfError` property is designed for statistical observations, making it a natural fit for validation deviation scores.

---

## 6. Next Steps After This Mapping

1. Embed schema.org `@context` and `@type` directly in production JSON output files (in downstream implementation repos).
2. Publish `DefinedTermSet` as a standalone JSON-LD document for external reference.
3. Expose `DataCatalog` metadata at the repository root (`https://raw.githubusercontent.com/.../catalog.json`) for dataset discovery.
4. Validate all JSON-LD output using the [Google Rich Results Test](https://search.google.com/test/rich-results) or schema.org validator.

---

**Status**: Formalized Mapping
**Governance**: Compliant with "Lean PSI Validator" principles — no new abstractions, only semantic annotations on existing data structures.
