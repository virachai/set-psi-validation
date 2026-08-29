---
name: validation-engine-categorical-fix
description: Resolved Pandas4Warning in validation_engine.py by correctly defining regime categories including 'Unclassified'.
metadata:
  type: user
---

**Why:** The previous implementation caused `Pandas4Warning` because the `VALID_REGIMES` list was missing the 'Unclassified' regime, which was being passed in the data.

**How to apply:** Updated `VALID_REGIMES` constant in `scripts/python/validation_engine.py` to include `"Unclassified"` and ensured `pd.Categorical` uses the complete list. Verified with `pytest` that warnings are eliminated and tests pass.
