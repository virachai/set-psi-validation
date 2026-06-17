---
name: Agents vs Claude Directory Audit
description: Full audit of .agents/ and .claude/ directories — duplicate structure confirmed, architecture decision to keep .agents/ as canonical shared location.
type: project
---

# Agents vs Claude Directory Audit

**Date:** 2026-06-17
**Status:** Completed

## Context

Investigated whether `.agents/` and `.claude/` directories contain duplicate files that could be cleaned up. Both are in `.gitignore` — not tracked in git, purely local.

## Findings

- **100% identical duplicates** across all subdirectories: rules (11 files), agents (1 definition), skills (32+ directories), agent-memory
- **Unique to `.agents/`**: `inventory.md`, `README.md`, `rules/no-fluff.md`, `workflows/` (2 files)
- **Unique to `.claude/`**: `settings.local.json`, `spec/`, `template/SKILL.md`, `THIRD_PARTY_NOTICES.md`, `README.md`

## Decision

- `.agents/` is the **canonical shared location** for ALL agents (skills, rules, agent definitions, workflows)
- `.claude/` is **Claude Code-specific config** (settings, templates, spec) — other agents don't need it
- The duplication is intentional and correct: agents look in `.agents/`, Claude Code also reads `.claude/` by convention
- **No files were deleted.** The parallel structure is the right architecture.

## Why

Claude Code natively loads from `.claude/`, while other agents (Cline, etc.) may reference `.agents/`. Both must exist to serve their respective consumers. Since both are gitignored, duplication costs nothing in terms of repo size.
