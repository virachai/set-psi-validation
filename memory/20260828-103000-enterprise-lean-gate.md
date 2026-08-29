---
name: 20260828-103000-enterprise-lean-gate
description: Rejected "enterprise-grade" infrastructure pillars (Airflow/ELK/Vault) per lean governance; adopted CI test gate + Mermaid docs instead.
type: feedback
---

**Rule:** The PSI validator stays lean — no Airflow/Temporal orchestration, ELK/Loki logging stacks, or Vault. GitHub Actions cron + GitHub Secrets + app.jsonl remain the orchestration and secrets layers.

**Why:** The "lv99 enterprise-grade" agenda (5 pillars) conflicts with `010-lean-psi-validator-governance.md`, which prohibits cross-repo systems and enterprise/layer architecture. The pipeline's only meaningful SLO is "data ingestion failed" — alerting on that is handled by workflow run failure, not a metrics stack.

**How to apply:**
- Orchestration = existing `intraday-pipeline.yml` (dual-zone ICT/UTC, idempotent range windows).
- Test seam: `fetch_setsmart_eod()` accepts optional `transport` (httpx.BaseTransport) for `httpx.MockTransport` stubbing — do not monkeypatch `httpx.Client` globally.
- Integration contract lives in `tests/python/test_setsmart_integration.py` (request params/headers, auth/empty/HTTP/timeout failures, full ATO→ATC→regime→file schema). It runs in `python-quality.yml` (pytest -q) and in the intraday pipeline pre-commit gate.
- Architecture docs = Mermaid in `docs/FLOW.md` (flowchart + sequenceDiagram); ASCII block ids (`id="flow0"`) preserved on the fences.
