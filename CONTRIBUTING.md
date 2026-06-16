# Contributing to SET PSI Validation

Thank you for your interest in contributing to the **SET PSI Validation** project! As the "Truth Layer" for the PSI ecosystem, we maintain high standards for data integrity and engineering rigor.

## 🏛️ Engineering Principles

1.  **Zero Lookahead Bias:** All validation logic must strictly separate prediction data (Pre-ATO) from market reality (ATO/ATC). No code should ever allow future data to influence past observations.
2.  **Statistically Sound:** Changes to the `validation_engine.py` must be backed by quantitative reasoning (see `docs/011-rfc-pipeline-refinements-v01.md`).
3.  **Semantic Integrity:** We use `schema.org` mappings. Ensure all JSON-LD outputs remain compliant with our internal schemas in `docs/02_research_reports/`.

## 🛠️ Development Setup

We use `uv` for dependency management and Python 3.12+.

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Linting & Formatting
uv run ruff check .
uv run ruff format .
```

## 📈 Contribution Workflow

1.  **Check the RFCs:** Look at `docs/` for active RFCs before proposing major architectural changes.
2.  **Open an Issue:** Discuss significant changes before implementation.
3.  **Strict Schedule:** If you are testing live data capture, remember the SET market hours (ICT):
    *   **09:00:** Prediction Capture.
    *   **10:00:** Market Open (ATO).
    *   **16:30:** Market Close (ATC).
4.  **Verification:** Every Pull Request must include a successful run of `scripts/sh/test.sh`.

## 🎨 Coding Standards

*   Use Python type hints for all functions.
*   Follow PEP 8 via `ruff`.
*   Maintain comprehensive docstrings for validation logic.

---

**Governance:** This project follows the "Lean PSI Validator" principles: Actionable, Measurable, and Standardized.
