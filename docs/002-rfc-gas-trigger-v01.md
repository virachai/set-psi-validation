---
rfc_id: 002
title: Migration to Google Apps Script (GAS) Triggered Workflow
status: Draft
date: 2026-06-18
---

# RFC: Migration to Google Apps Script (GAS) Triggered Workflow

## 1. Problem Statement

The current GitHub Actions `schedule` trigger is subject to "Queue Delay" and potential suspension due to repository inactivity. This causes intermittent failures in capturing market data (ATO/ATC) and validating PSI regimes, leading to gaps in the validation pipeline.

## 2. Proposed Solution

Migrate the primary trigger mechanism from GitHub Actions `schedule` to a Google Apps Script (GAS) based trigger. GAS will act as a reliable "ping" service that invokes the GitHub `repository_dispatch` API at precise intervals.

## 3. Technical Implementation

- **Trigger**: GAS Time-driven Triggers (reliable execution).
- **Interface**: GitHub `repository_dispatch` API.
- **Workflow Update**:
  - Add `repository_dispatch` to `intraday-pipeline.yml`.
  - Update `Determine Step` logic to parse `client_payload`.
- **Security**: Use GitHub Personal Access Token (PAT) stored as a script property in GAS.

## 4. Benefits

- **Deterministic Execution**: Eliminates "Cron Delay" issues.
- **Observability**: GAS provides clear execution logs independent of GitHub's internal scheduler.
- **Control**: Ability to trigger specific steps or "all" on-demand via the GAS interface.

## 5. Alternatives Considered

- **GitHub Actions `workflow_dispatch`**: Manual trigger only (not automated).
- **External Cron Services (e.g., Cron-job.org)**: Adds third-party dependency; GAS is preferred as it is integrated and free.

## 6. Implementation Plan

1. Update `intraday-pipeline.yml` to support `repository_dispatch`.
2. Configure GitHub PAT.
3. Deploy GAS script with time-driven triggers for 09:00, 10:00, 14:00, 16:30, 17:00 ICT.
