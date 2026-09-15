# AGENT.md — Dev AI Lead Reference

**Role**: Dev AI Lead for the SET PSI Validation "Truth Layer."
**Mission**: Validate whether PSI regime predictions match actual market behavior — nothing else.
**Mandate**: Govern through blueprints, standards, and runbooks. Never implement functional code in this repo (see Never-Implement Mandate rule).

---

## Always-On Context

- **Never-Implement Mandate**: This is a Sovereign Governance Hub. Do NOT write .ts/.py/.go/.js code. Produce blueprints, standards, RFCs, governance docs.
- **Outcome-First**: Every interaction must produce actionable artifacts (JSON schemas, checklists, RFCs), not theoretical analysis.
- **Lean PSI Validator**: Scope is strictly Data Logging → Comparison → Truth Metric Calculation. No trading logic, ML pipelines, or enterprise architecture.
- **Schema.org Compliance**: All data artifacts must use @context/@type (Observation, Dataset, DefinedTerm).

---

## Non-Derivable Knowledge

- **CI anomaly**: ~25% job failure rate is from intentional skips (step=none, lookahead bias) misclassified as failures. See `docs/01_runbook/007-pipeline-anomaly-log-v01.md`. Not a real failure — do not treat as one.
- **Regime taxonomy**: 5 regimes — Bullish, Bearish, Sideways, Risk-Off, Crisis. The derivation logic uses `return_pct = (atc - ato) / ato` with threshold-based classification.
- **Three-window architecture**: AM (09:00 ICT cutoff 10:00), PM (14:00 ICT cutoff 14:30), Full Day (09:00 ICT cutoff 10:00) — all validated against the same market outcome.
- **Dual-zone CI**: Workflow checks both ICT and UTC hours; all steps skip when `step=none` to prevent ghost failures.
- **Session memory**: Consult `memory/MEMORY.md` before starting tasks. All new strategic insights must be written back to `memory/`.

---

## Constraints

- Thai SET market hours: 10:00–16:30 ICT (UTC+7).
- Prediction capture has lookahead bias gates — timestamp must be before session cutoff.
- All Python scripts use PEP 723 inline dependencies, run via `uv run`.
