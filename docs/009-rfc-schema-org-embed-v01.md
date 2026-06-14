# RFC: Embed Schema.org Metadata in PSI Validation Output

- **Status**: Draft
- **Type**: Standards & Interoperability
- **Authors**: AI Engineering Lead
- **Created**: 2026-06-14
- **Governance**: Compliant with "Lean PSI Validator" and "Never-Implement" mandates

---

## 1. Summary

Add schema.org JSON-LD annotations to all PSI Validation output artifacts — predictions, market outcomes, and validation evaluations — plus publish a standalone Regime Taxonomy and a root-level DataCatalog for dataset discovery.

This RFC defines the **contract** (what to produce). Actual implementation happens in the downstream sub-repository (`set-psi-validation` implementation fork).

---

## 2. Motivation

### 2.1 Current State

The existing JSON schemas (`004`, `005`, `006`) use simple key-value objects without semantic context:

```json
{
  "predictedRegime": "RISK_OFF",
  "psiScore": 0.41
}
```

These are machine-readable but not semantically self-describing. A downstream consumer cannot determine that `predictedRegime` references a controlled taxonomy, or that `psiScore` is bounded between [0, 1], without reading external documentation.

### 2.2 Why Now

The schema.org mapping has been formalized in `docs/research_reports/008-schema-org-mapping-v01.md`. This RFC converts that mapping from analysis into an actionable standard.

### 2.3 Expected Benefits

| Benefit                     | Impact                                                                                            |
| :-------------------------- | :------------------------------------------------------------------------------------------------ |
| **Self-describing data**    | Each JSON file carries its own semantic context via `@context` and `@type`.                       |
| **Dataset discoverability** | `DataCatalog` at root enables Google Dataset Search and automated crawlers to index PSI data.     |
| **Cross-repo alignment**    | PSI Engine, Validation, and Dashboard share a common vocabulary (the `DefinedTermSet`).           |
| **Future-proofing**         | Adding new regimes or metrics requires only extending the `DefinedTermSet`, not changing schemas. |

---

## 3. Specification: 3 Artifacts

### 3.1 Artifact A — Prediction Snapshot (Embedded JSON-LD)

**File:** `predictions/YYYY-MM-DD.json`

**Current:**

```json
{
  "timestamp": "2026-06-14T09:00:00+07:00",
  "date": "2026-06-14",
  "predictedRegime": "RISK_OFF",
  "psiScore": 0.41,
  "modelId": "psi-engine-v1"
}
```

**Target:**

```json
{
  "@context": "https://schema.org",
  "@type": "Observation",
  "name": "PSI Prediction 2026-06-14",
  "observationDate": "2026-06-14T09:00:00+07:00",
  "measuredProperty": {
    "@type": "DefinedTerm",
    "name": "Predicted Regime",
    "inDefinedTermSet": "https://raw.githubusercontent.com/user/set-psi-validation/main/docs/010-regime-taxonomy-v01.json"
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

**Rules:**

1. `@context` MUST be `"https://schema.org"`.
2. `@type` MUST be `"Observation"`.
3. `measuredProperty` MUST reference the `Predicted Regime` term from the `DefinedTermSet`.
4. `variableMeasured` MUST contain the PSI score with explicit `minValue`/`maxValue`.
5. `measurementMethod` MUST identify the PSI engine version.

---

### 3.2 Artifact B — Market Outcome (Embedded JSON-LD)

**File:** `market-data/YYYY-MM-DD.json`

**Current:**

```json
{
  "date": "2026-06-14",
  "atoPrice": 1450.2,
  "atcPrice": 1438.1,
  "returnPct": -0.83,
  "volatilityIndex": 1.95,
  "actualRegime": "RISK_OFF"
}
```

**Target:**

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
    "inDefinedTermSet": "https://raw.githubusercontent.com/user/set-psi-validation/main/docs/010-regime-taxonomy-v01.json"
  },
  "variableMeasured": [
    {
      "@type": "QuantitativeValue",
      "name": "ATO Price",
      "value": 1450.2,
      "unitText": "SET Index Points"
    },
    {
      "@type": "QuantitativeValue",
      "name": "ATC Price",
      "value": 1438.1,
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

**Rules:**

1. Price fields (`atoPrice`, `atcPrice`) MUST use `QuantitativeValue` with `unitText: "SET Index Points"`.
2. `measuredProperty` MUST reference the `Actual Regime` term from the `DefinedTermSet`.
3. `observationPeriod` SHOULD use ISO 8601 interval format covering the ATO→ATC window.

---

### 3.3 Artifact C — Validation Evaluation (Embedded JSON-LD)

**File:** `validation/YYYY-MM-DD.json`

**Current:**

```json
{
  "date": "2026-06-14",
  "predictionId": "predictions/2026-06-14.json",
  "outcomeId": "market-data/2026-06-14.json",
  "isCorrect": true,
  "deviationScore": 0.0
}
```

**Target:**

```json
{
  "@context": "https://schema.org",
  "@type": "Observation",
  "name": "Validation Evaluation 2026-06-14",
  "observationDate": "2026-06-14T17:00:00+07:00",
  "observationAbout": [
    {
      "@id": "https://raw.githubusercontent.com/user/set-psi-validation/main/predictions/2026-06-14.json"
    },
    {
      "@id": "https://raw.githubusercontent.com/user/set-psi-validation/main/market-data/2026-06-14.json"
    }
  ],
  "measuredProperty": {
    "@type": "DefinedTerm",
    "name": "Regime Prediction Accuracy",
    "inDefinedTermSet": "https://raw.githubusercontent.com/user/set-psi-validation/main/docs/010-regime-taxonomy-v01.json"
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

**Rules:**

1. `observationAbout` MUST contain both the prediction and outcome resource URLs.
2. `marginOfError` MUST contain the `deviationScore` value as a `QuantitativeValue`.
3. This is the **only** artifact that uses `marginOfError` — it is the strongest 1:1 mapping found in the schema.org analysis.

---

## 4. Specification: Standalone Artifacts

### 4.1 Artifact D — Regime Taxonomy (Standalone JSON-LD)

**File:** `docs/010-regime-taxonomy-v01.json`

This file is published once and updated only when the regime taxonomy changes (rare). All other artifacts reference it via `inDefinedTermSet`.

```json
{
  "@context": {
    "psi": "https://psi-validation.dev/definitions/"
  },
  "@type": "DefinedTermSet",
  "name": "PSI Market Regime Classification",
  "description": "Taxonomy of market regime labels used by the PSI (Pressure-Signal Index) system for the SET (Stock Exchange of Thailand) market.",
  "url": "https://raw.githubusercontent.com/user/set-psi-validation/main/docs/010-regime-taxonomy-v01.json",
  "hasDefinedTerm": [
    {
      "@type": "DefinedTerm",
      "@id": "psi:regime/bullish",
      "name": "Bullish",
      "termCode": "BULLISH",
      "description": "Strong positive intraday return with broad-based market strength."
    },
    {
      "@type": "DefinedTerm",
      "@id": "psi:regime/bearish",
      "name": "Bearish",
      "termCode": "BEARISH",
      "description": "Consistent intraday decline with weak closing relative to ATO."
    },
    {
      "@type": "DefinedTerm",
      "@id": "psi:regime/sideways",
      "name": "Sideways",
      "termCode": "SIDEWAYS",
      "description": "Low directional movement in a range-bound trading session."
    },
    {
      "@type": "DefinedTerm",
      "@id": "psi:regime/risk-off",
      "name": "Risk-Off",
      "termCode": "RISK_OFF",
      "description": "Defensive behavior with increased volatility and negative bias."
    },
    {
      "@type": "DefinedTerm",
      "@id": "psi:regime/crisis",
      "name": "Crisis",
      "termCode": "CRISIS",
      "description": "Sharp downside move with extreme volatility spike."
    }
  ]
}
```

**Rules:**

1. Each `DefinedTerm` MUST have a unique `@id` using the `psi:` namespace.
2. `termCode` MUST be uppercase snake_case for machine consumption.
3. `description` MUST define the regime condition in plain language.

---

### 4.2 Artifact E — DataCatalog (Standalone JSON-LD)

**File:** `catalog.json` (repo root)

Published once and updated when datasets are added/removed.

```json
{
  "@context": "https://schema.org",
  "@type": "DataCatalog",
  "name": "SET PSI Validation Data Catalog",
  "description": "Complete catalog of all data artifacts in the PSI (Pressure-Signal Index) validation pipeline for the Stock Exchange of Thailand.",
  "url": "https://raw.githubusercontent.com/user/set-psi-validation/main/catalog.json",
  "dataset": [
    {
      "@type": "Dataset",
      "name": "PSI Predictions",
      "description": "Pre-ATO regime forecast snapshots.",
      "url": "https://github.com/user/set-psi-validation/tree/main/predictions",
      "variableMeasured": ["PSI Score", "Predicted Regime"],
      "measurementTechnique": "PSI Engine v1"
    },
    {
      "@type": "Dataset",
      "name": "Market Outcomes",
      "description": "Observed ATO/ATC intraday market data.",
      "url": "https://github.com/user/set-psi-validation/tree/main/market-data",
      "variableMeasured": [
        "ATO Price",
        "ATC Price",
        "Return %",
        "Intraday Volatility"
      ]
    },
    {
      "@type": "Dataset",
      "name": "Validation Evaluations",
      "description": "Prediction vs outcome comparison records.",
      "url": "https://github.com/user/set-psi-validation/tree/main/validation",
      "variableMeasured": ["Is Correct", "Deviation Score"],
      "measurementTechnique": "Regime comparison against deterministic derivation rules."
    },
    {
      "@type": "Dataset",
      "name": "Aggregated Metrics",
      "description": "Rolling accuracy, F1, precision, recall, and confusion matrix.",
      "url": "https://github.com/user/set-psi-validation/tree/main/reports",
      "variableMeasured": ["Accuracy", "F1 Score", "Precision", "Recall"]
    }
  ]
}
```

---

## 5. Implementation Plan

Per the "Never-Implement" mandate (`.claude/rules/never-implement-mandate.md`), this RFC defines the **contract only**. Implementation occurs in the downstream sub-repository.

### Phase 1 — Standalone Artifacts (Low Effort)

| Artifact        | File                          | Action                       | Dependencies |
| :-------------- | :---------------------------- | :--------------------------- | :----------- |
| Regime Taxonomy | `docs/010-regime-taxonomy-v01.json` | Create new file              | None         |
| DataCatalog     | `catalog.json`                | Create new file in repo root | None         |

### Phase 2 — Embedded JSON-LD in Validation Pipeline

| Artifact              | File                 | Action                                                         | Dependencies                         |
| :-------------------- | :------------------- | :------------------------------------------------------------- | :----------------------------------- |
| Prediction Snapshot   | `predictions/*.json` | Update serializer to emit `@context`/`@type`                   | Phase 1 (for `inDefinedTermSet` URL) |
| Market Outcome        | `market-data/*.json` | Update serializer to emit `@context`/`@type`                   | Phase 1                              |
| Validation Evaluation | `validation/*.json`  | Update serializer to emit `@context`/`@type` + `marginOfError` | Phase 1                              |

### Phase 3 — Verification

| Step                 | Action                                                           | Tool                                                                    |
| :------------------- | :--------------------------------------------------------------- | :---------------------------------------------------------------------- |
| Validate JSON-LD     | Check all output files against schema.org spec                   | [JSON-LD Playground](https://json-ld.org/playground/)                   |
| Test discovery       | Confirm `catalog.json` is parseable by dataset search crawlers   | [Google Rich Results Test](https://search.google.com/test/rich-results) |
| Cross-repo alignment | Verify PSI Engine and Dashboard can consume the `DefinedTermSet` | Manual review                                                           |

---

## 6. Backward Compatibility

- All existing fields (`predictedRegime`, `atoPrice`, etc.) are **preserved** in the target format.
- `@context` and `@type` are additive — they do not break existing parsers.
- Downstream consumers that read `data.predictedRegime` will still work unchanged.

**No breaking changes.**

---

## 7. Open Questions

| Question                                                                                                    | Decision Needed By   |
| :---------------------------------------------------------------------------------------------------------- | :------------------- |
| 1. Should `catalog.json` live at repo root or under `docs/`?                                                | Implementation phase |
| 2. Should the `@id` URLs point to `raw.githubusercontent.com` or a custom domain?                           | Infrastructure setup |
| 3. Should the `DefinedTermSet` include `sameAs` links to external financial ontologies (e.g., FIBO, FROnt)? | Future extension     |

---

## 8. References

| Document                      | Link                                                              |
| :---------------------------- | :---------------------------------------------------------------- |
| Schema.org Mapping            | `docs/research_reports/008-schema-org-mapping-v01.md`             |
| Prediction Snapshot Schema    | `docs/research_reports/005-prediction-snapshot-schema-v01.json`   |
| Market Outcome Schema         | `docs/research_reports/004-market-outcome-schema-v01.json`        |
| Validation Evaluation Schema  | `docs/research_reports/006-validation-evaluation-schema-v01.json` |
| Lean PSI Validator Governance | `.claude/rules/010-lean-psi-validator-governance.md`              |
| Never-Implement Mandate       | `.claude/rules/never-implement-mandate.md`                        |
| schema.org Observation        | https://schema.org/Observation                                    |
| schema.org DefinedTermSet     | https://schema.org/DefinedTermSet                                 |
| schema.org DataCatalog        | https://schema.org/DataCatalog                                    |
| JSON-LD Playground            | https://json-ld.org/playground/                                   |
