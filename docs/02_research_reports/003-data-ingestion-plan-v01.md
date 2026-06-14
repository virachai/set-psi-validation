# PSI Data Ingestion Plan (v01)

## 🎯 Objective

Establish a deterministic process to ingest raw market data into the standardized JSON schemas, ensuring data integrity for the validation pipeline.

## 📥 Data Sources

1. **PSI Predictions**: Pre-market forecast files (Format: `predictions/YYYYMMDD_psi.json`).
2. **Market Data**: Intraday market data (Format: `market-data/YYYYMMDD_market.csv`).

## 🔄 Ingestion Workflow

1. **Extraction**:
   - `extract_pdf.py`: Scrape/Parse raw SET market data.
   - `predictions_loader.py`: Read raw PSI forecast JSONs.
2. **Normalization**:
   - Map `ATO_Price`, `ATC_Price` to `market-outcome-schema-v01.json`.
   - Map `predictedRegime` to `prediction-snapshot-schema-v01.json`.
3. **Validation**:
   - Run schema validation against the defined JSON schemas.
   - Flag missing or malformed records.
4. **Storage**:
   - Save validated records to `data/processed/YYYYMMDD_validation_ready.json`.

## ⚙️ Governance Compliance

- **Lean**: No complex database required; use simple JSONL/JSON file storage.
- **Deterministic**: Ingestion scripts must be idempotent (re-running on the same file produces identical output).
- **Environment**: All Python tasks must be executed via `uv run` as per `python-venv-governance.md`.

---

**Status**: Plan for Review
**Governance**: Compliant with "Lean PSI Validator" principles.
