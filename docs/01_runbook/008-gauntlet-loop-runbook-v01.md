# 008-gauntlet-loop-runbook-v01.md (Level 99 Enterprise-Grade)

## 🎯 Executive Summary & Objective

This runbook establishes the mission-critical Standard Operating Procedure (SOP) for executing **Gauntlet Loops** within the PSI Market Regime Validation Pipeline. The Gauntlet Loop protocol pairs autonomous multi-agent builders with hyper-adversarial critics, driven by an automated evaluation gate (`/loop`), to ensure zero-defect implementations, absolute alignment with the Lean PSI Validator Governance, and mathematically rigorous validation standards.

---

## 🏛️ Enterprise Architecture & Governance Principles

1. **Outcome-First Mandate**: Every gauntlet iteration must produce a verifiable, measurable artifact (code, test suite, benchmark score, or audit report). Theoretical speculation is strictly prohibited.
2. **The Immutable Bar Standard**: No loop initiates without a concrete, fetchable, and comparable benchmark (e.g., historical Thai Stock Market ATO/ATC volatility benchmarks, published alpha decay equations, or golden reference datasets).
3. **Adversarial Separation of Concerns**: The Builder agent and the Critic agent operate in isolated context windows. The Critic has zero knowledge of the Builder's internal reasoning, enforcing pure black-box comparative judgment against the reference bar.
4. **Deterministic Convergence**: Loops terminate exclusively upon cryptographic/blind comparison success against the bar or explicit human override—never upon arbitrary round counts.

---

## 🔄 The 5-Phase Gauntlet Lifecycle

```textplain
[Phase 1: Scope & Bar Definition]
             ↓
[Phase 2: Atomic Decomposition]
             ↓
[Phase 3: Parallel Builder & Critic Execution]
             ↓
[Phase 4: Blind A/B Evaluation & Gap Analysis]
             ↓
[Phase 5: Convergence & Production Promotion]
```

### Phase 1: Scope & Bar Definition

- **Objective**: Establish the exact boundaries and the golden reference bar.
- **Action**: Define the measurable success criteria (e.g., F1-score $\ge 0.85$, zero lookahead bias infractions, execution time $< 500\text{ms}$).

### Phase 2: Atomic Decomposition

- **Objective**: Break the complex feature or refactoring task into minimal, independent, judgeable components.
- **Action**: Isolate components into single-responsibility units (e.g., Data Ingestion, Lookahead Guardrail, Regime Classification Engine, Truth Metric Calculator).

### Phase 3: Parallel Builder & Critic Execution

- **Objective**: Execute concurrent implementation and adversarial stress-testing.
- **Action**: Fan out builders to generate code/artifacts, while independent critic agents inspect actual runtime outputs and test coverages.

### Phase 4: Blind A/B Evaluation & Gap Analysis

- **Objective**: Unbiased comparative scoring against the reference bar.
- **Action**: Strip metadata and labels; present candidate output side-by-side with the golden reference to the Critic. The Critic records a binary win/loss and explicitly names the single largest remaining delta.

### Phase 5: Convergence & Production Promotion

- **Objective**: Finalize and integrate verified components.
- **Action**: Once the Critic selects the candidate blind across all atomic sub-components, commit artifacts to the repository and record metrics in the audit trail.

---

## 📋 Standard Prompt Template (Enterprise Edition)

```markdown
Build [GOAL] for the PSI Validation Pipeline.

The benchmark bar is [CONCRETE FETCHABLE REFERENCE, e.g., scripts/python/validation_engine.py reference implementation + historical SET ATO/ATC benchmark JSON]. Compare against the actual benchmark outputs directly, not against descriptions.

Deconstruct this work into the smallest atomic components testable in isolation. For each component, fan out an independent builder and a separate harsh critic with fresh context. The critic inspects the realized output, compares it blind against the benchmark bar with all identifying labels stripped, determines definitively which output is superior, and specifies the single largest remaining deficiency. If our output does not decisively win, iterate.

Enforce zero lookahead bias, strict type-hinting, PEP 723 compliance, and complete unit test coverage via pytest under uv run.

/loop on each atomic component until the critic validates our output wins blind. Never terminate based on an arbitrary iteration count.

Maintain a live progress log in docs/01_runbook/ and invoke ultracode multi-agent orchestration.
```

---

## 🛠️ Operational Best Practices & Anti-Patterns

| Recommended Practice (`DO`)                                                                | Enterprise Prohibitions (`DO NOT`)                                                       |
| :----------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------- |
| **Ground the Bar:** Use concrete paths, historical JSON datasets, or verified math models. | **Vague References:** Never use subjective descriptions like "industry-standard code".   |
| **Strict Isolation:** Ensure critics operate without builder transcripts.                  | **Self-Grading:** Never allow a builder agent to evaluate its own code quality.          |
| **Binary Verdicts:** Require clear win/loss determinations from the critic.                | **Soft Scoring:** Avoid inflation metrics (e.g., "7/10 score") that bypass hard gates.   |
| **Audit Logging:** Record every iteration's delta and verdict in session journals.         | **Silent Truncation:** Never suppress failed iterations or skip adversarial refutations. |

---

## 🔍 Failure Mode & Effects Analysis (FMEA)

1. **Hallucinated Reference Bar**:
   - _Symptom_: Critic approves substandard code because the benchmark data was simulated or guessed.
   - _Mitigation_: Require all bar references to point to verified files in `tests/fixtures/` or immutable historical logs.
2. **Infinite Loop / Stagnation**:
   - _Symptom_: Builder and critic alternate without making progress due to over-constrained validation rules.
   - _Mitigation_: Human-in-the-loop intervention to refine atomic boundaries or relax non-functional constraints.
3. **Lookahead Leakage**:
   - _Symptom_: Optimizer accidentally references future intraday ticks during pre-market regime backtesting.
   - _Mitigation_: Mandatory execution of `scripts/python/predictions_loader.py` guardrail checks prior to critic sign-off.
