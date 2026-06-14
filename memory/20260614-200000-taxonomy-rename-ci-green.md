---
name: Taxonomy Renamed & CI Green
description: Renamed regime-taxonomy.jsonld to follow naming convention, updated all references, CI passing
type: project
---

Renamed `docs/regime-taxonomy.jsonld` → `docs/010-regime-taxonomy-v01.json` to comply with the `NNN-kebab-case-vNN` naming convention. Updated all references across the codebase.

**Changes:**

- Renamed file and updated its internal `url` field
- Updated `REGIME_TAXONOMY_URL` in `capture_market.py` and `predictions_loader.py`
- Updated workflow git-add path in `intraday-pipeline.yml`
- Updated data files: `market-data/2026-06-14.json`, `predictions/2026-06-14.json`
- Updated docs: `009-rfc-schema-org-embed-v01.md`, `001-github-setup-v01.md`

**Verified:**

- RapidAPI endpoint (`set-market-psi-api.p.rapidapi.com`) returns valid schema.org Observation with updated taxonomy URL
- GitHub Actions `Python Quality` workflow — Status: Success (all 6 steps pass)
- Only warning is Node.js 20 deprecation (deadline June 16, 2026)
