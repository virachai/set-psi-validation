# RFC: Truth Artifact Addressing and Resolution

**Status:** Accepted (Phase 1–2 implemented; Phase 3–4 deferred)  
**Version:** v01  
**Date:** 2026-10-04  
**Scope:** `predictions/`, `market-data/`, `validation/`, audit and resolver logic

## 1. Problem

The PSI Truth Layer currently uses filename-derived dates and glob ordering in several places to resolve prediction and market artifacts. This is convenient, but it is weaker than validating the identity carried by the artifact itself.

A file can have a plausible filename while its payload contains a different observation date, observation period, session, or provenance. If a resolver trusts the filename first, a malformed or manually altered artifact can be selected as truth.

Concrete gaps found in the code (2026-10-04):

- `validation_engine.find_latest_market_file` returned the last `*-atc.json` by glob order without reading the payload, so an incomplete, wrong-date, or window-guard-bypassed capture could be scored as Actual Truth.
- `validation_engine.find_latest_prediction_file` accepted a prediction with no `observationDate`/`timestamp`, skipping the lookahead gate (fail open).
- `validation_engine.load_json` raised on malformed JSON, aborting the whole run instead of rejecting one candidate.

The repository therefore needs a single, deterministic addressing contract for truth artifacts.

## 2. Goals

1. Define one canonical address for every prediction, market, and validation artifact.
2. Make artifact identity derive from validated payload fields, not filename alone.
3. Reject mismatched filename/payload addresses.
4. Prevent lookahead and cross-session substitution during resolution.
5. Preserve enough provenance to explain why a specific artifact was selected.
6. Keep the implementation lean and compatible with existing repository paths.

## 3. Non-goals

- Redesigning the PSI regime taxonomy.
- Changing regime derivation thresholds.
- Replacing the current market-data provider.
- Introducing a database.
- Changing the public dashboard contract unless required by implementation.

## 4. Canonical Address

The canonical logical address is:

```text
<artifact-type>/<observation-date>/<session>/<role>
```

Where:

- **artifact-type** = `prediction`, `market`, or `validation`
- **observation-date** = trading date in `YYYY-MM-DD`
- **session** = canonical PSI session identifier
- **role** identifies the required observation within that session.

For the current full-day truth path, the minimum canonical market address is:

```text
market/2026-10-02/full_day/atc
```

The physical filename remains an implementation detail. A timestamped filename such as `2026-10-02-224825-atc.json` must resolve to the same logical address only after its payload passes validation.

## 5. Address Fields

Required fields differ per artifact type. Existing artifacts do not all carry every field (market captures have no `session`; predictions have no `status`), so a resolver MUST validate only the fields listed for that type:

| Field | Prediction | Market (ATC) | Validation |
|---|---|---|---|
| `date` (ICT trading date) | MUST equal requested date | MUST equal requested date | MUST equal requested date |
| `observationDate` / `timestamp` | MUST exist and pass the prediction window gate | — | — |
| `session` | MUST equal requested session (filename) | implied by `role` (`atc` = `full_day`) | MUST equal requested session |
| `status` | — | MUST be `complete` | — |
| `windowGuardBypassed` | — | MUST be absent/false in production | — |
| `observationPeriod` | — | SHOULD cover 10:00–16:30 ICT (deferred check) | — |
| `actualRegime` | — | MUST exist to be used as Actual Truth | — |
| `observationAbout` | — | — | MUST reference source prediction/market ids (already emitted) |
| provenance | — | SHOULD (deferred, §8) | — |

`date` is used rather than `observationDate[:10]` because `observationDate` is UTC: a 05:00 ICT prediction carries the previous UTC date.

If the same semantic value is represented both as a flat field and a Schema.org field, the resolver MUST reject conflicting values rather than choosing one silently.

## 6. Resolution Rules

### 6.1 Prediction resolution

Given `(date, session)`:

1. Enumerate candidate prediction files.
2. Parse each candidate.
3. Validate its payload address.
4. Discard candidates with malformed JSON, invalid timestamps, wrong date, wrong session, or out-of-window prediction timestamps.
5. Select the deterministic latest valid candidate within the permitted prediction window.
6. If no candidate remains, return no prediction.

Filename prefixes MUST NOT be sufficient evidence of validity.

### 6.2 Market truth resolution

Given `(date, session, role)`:

1. Enumerate candidate market files.
2. Parse each candidate.
3. Require `status == complete`.
4. Validate embedded observation identity.
5. Validate the observation period against the requested role.
6. Reject records marked as bypassed unless an explicit audit/backfill mode is being used.
7. Require the fields needed to derive or expose Actual Regime.
8. Select the deterministic latest valid candidate.
9. If no valid candidate remains, fail closed.

A legacy filename fallback MAY remain temporarily, but it MUST still pass payload validation before being accepted.

### 6.3 Validation resolution

Validation records MUST reference the exact prediction and market artifact identities used to create the evaluation. This is already satisfied: `validation_engine` emits `observationAbout: [{"@id": "predictions/<file>"}, {"@id": "market-data/<file>"}]`.

A validation record MUST NOT be reconstructed by independently choosing “latest” files after the fact when an existing validation artifact already records the source identities.

## 7. Filename Contract

Physical filenames SHOULD remain timestamped because they are useful for auditability and collision avoidance.

Recommended forms:

```text
predictions/YYYY-MM-DD-HHMMSS-<session>.json
market-data/YYYY-MM-DD-HHMMSS-<role>.json
validation/YYYY-MM-DD-HHMMSS-<session>.json
```

The filename date is a consistency check, not the source of truth.

A filename/payload mismatch is an integrity error.

## 8. Provenance

New market artifacts SHOULD carry a provenance object containing, at minimum:

```json
{
  "provider": "yahoo",
  "fetchedAt": "2026-10-04T16:30:12+07:00",
  "sourceGranularity": "daily",
  "captureMode": "atc"
}
```

For a source that cannot verify the official auction print, the artifact MUST make that limitation explicit. A daily-bar close MUST NOT be represented as independently verified ATC auction truth.

## 9. Backfill and Bypass

Backfills are permitted only as explicitly marked artifacts.

If `PSI_BYPASS_WINDOW_GUARD=true` was used, the resulting record MUST carry:

```json
{
  "windowGuardBypassed": true
}
```

Such records MUST be excluded from normal production truth resolution unless the caller explicitly requests audit/backfill mode.

The bypass flag is evidence about capture procedure; it is not proof that the resulting market value is valid.

## 10. Failure Semantics

Resolvers MUST fail closed:

- malformed JSON → reject candidate
- missing required identity → reject candidate
- date mismatch → reject candidate
- session mismatch → reject candidate
- invalid observation period → reject candidate
- incomplete market artifact → reject candidate
- bypassed production artifact → reject candidate
- no valid candidate → return no truth / skip validation

The system MUST NOT silently substitute a nearby date, session, or later observation.

## 11. Audit Requirements

`audit_truth_layer.py` SHOULD use the same address-validation primitives as the production resolver.

The audit MUST detect at least:

- filename date vs payload date mismatch
- prediction window violations
- market observation-period mismatch
- incomplete market artifacts
- conflicting flat vs Schema.org identity fields
- bypassed artifacts presented as production truth
- validation records whose referenced source artifacts do not exist

This avoids having an audit implementation that can disagree with the production resolver.

## 12. Implementation Plan

### Phase 1 — Shared address validator

Create a small, dependency-light module responsible for:

- parsing artifact identity
- validating date/session
- validating observation period
- validating completion state
- identifying bypassed artifacts

### Phase 2 — Resolver hardening

Update prediction and market resolution to use the shared validator.

### Phase 3 — Provenance preservation

Persist provider metadata from the capture layer into market artifacts.

### Phase 4 — Audit convergence

Refactor `audit_truth_layer.py` to call the same validation/resolution primitives.

### Phase 5 — Regression tests

Add adversarial tests for:

1. correct filename + wrong payload date
2. correct filename + wrong session
3. malformed observation period
4. incomplete market record
5. bypassed capture
6. duplicate candidates with deterministic selection
7. legacy filename with valid payload
8. validation record referencing a missing source

## 13. Acceptance Criteria

The RFC is implemented when:

- No production resolver accepts an artifact solely because its filename matches.
- Filename/payload address mismatches are rejected.
- Market truth resolution is fail-closed.
- Bypassed records cannot silently enter production metrics.
- New market records retain provider/fetch provenance.
- Audit and production resolution use the same identity rules.
- Adversarial timestamp/address tests pass.
- Existing valid artifacts continue to resolve without requiring a database migration.

## 14. Decision

Adopt **payload-validated logical addressing** as the Truth Layer contract.

Physical paths and timestamped filenames remain for storage and auditability, but they are no longer authoritative identity. The authoritative identity is the validated semantic address carried by the artifact payload.

This keeps the repository lean while closing the integrity gaps listed in §1.

## 15. Frozen Scope (2026-10-04)

Scope was frozen to the minimal change that stops wrong artifacts from being scored, per the lean PSI validator governance.

**Shipped (Phase 1–2, in `validation_engine.py`):**

- Market resolver: newest `*-atc.json` whose payload has `status == complete`, `date == requested date`, and no `windowGuardBypassed`; otherwise the next older candidate; none → no truth (validation skipped).
- Prediction resolver: payload `date` must equal the requested date; a missing timestamp now rejects the candidate (was fail open).
- `load_json`: malformed JSON rejects the candidate with a warning instead of aborting the run.
- Adversarial tests for §12 Phase 5 items 1, 4, 5, 6 and 7 plus missing timestamp and malformed JSON (`TestPayloadValidatedResolution`).
- Test fixtures updated to carry `status`/`date`/`timestamp`, matching what the capture layer actually writes.

**Deferred:**

- Phase 3 (provenance object): aids audit, does not change measured accuracy.
- Phase 4 (audit uses shared primitives): follows once the resolver rules settle.
- `observationPeriod` validation and flat-vs-Schema.org conflict detection (§5): no current artifact exhibits either failure.

**Rejected:** none.

**Verified:** all 10 existing market files (2026-09-08 … 2026-10-02) still resolve.
