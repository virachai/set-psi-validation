---
name: Schema.org Mapping Complete
description: Completed schema.org type mapping for all PSI validation data artifacts (Observation, DefinedTermSet, Dataset, etc.)
type: project
---

The schema.org mapping phase for the PSI validation pipeline is complete.

- **Core mapping**: Observation (prediction, outcome, validation) + DefinedTermSet (regime taxonomy) + Dataset/DataCatalog (data organization) + marginOfError (deviationScore)
- **4 docs updated/created**: 008-schema-org-mapping-v01.md (new), 004/005/006 JSON schemas (updated with @context/@type), 007-project-summary.md (updated), FLOW.md (updated)
- **Why it matters**: Enables semantic interoperability, dataset discovery, and self-documenting data artifacts without changing the existing lean architecture
- **Next**: Ready for downstream implementation — embed schema.org JSON-LD in production output files
