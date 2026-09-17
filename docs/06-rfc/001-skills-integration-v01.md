# RFC-001: Integrate Matt Pocock Engineering Skills Safely

**Status:** Proposed — Local Agent Execution
**Owner:** Local coding agent
**Date:** 2026-09-16

## Context

This repository already has an established `.agents/skills` ecosystem with custom skills, rules, agents, and governance. We evaluated the Matt Pocock skills repository exposed by `https://www.aihero.dev/skills` / `https://github.com/mattpocock/skills`.

The local environment has been upgraded to:

- Node.js `22.20.0`
- npm `10.9.3`
- `skills` CLI `1.5.26`

The CLI can successfully discover the upstream repository and currently reports 37 available skills. No upstream skill has been installed by this RFC yet.

## Objective

Add useful Matt Pocock engineering skills without overwriting, duplicating, or weakening the repository's existing skill/rule architecture.

## Candidate skills

Prioritize these nine candidates:

1. `code-review`
2. `codebase-design`
3. `diagnosing-bugs`
4. `domain-modeling`
5. `research`
6. `wayfinder`
7. `to-spec`
8. `to-tickets`
9. `implement`

Known overlap with existing local skills includes `tdd`, `handoff`, `grill-me`, `improve-codebase-architecture`, `setup-pre-commit`, and `git-guardrails-claude-code`. Do **not** blindly install overlapping skills.

## Required work

### 1. Baseline audit

Before modifying anything:

- inspect `.agents/skills/SKILLS_INDEX.md`
- inspect `.agents/skills/metadata.json`
- inspect relevant `.agents/rules/*`
- inspect `.claude/` skill/agent configuration if affected
- run `npx skills@latest list`
- record current git status

Do not discard or overwrite user changes.

### 2. Fetch/discover upstream

Use the skills CLI with Node `22.20.0`.

Preferred discovery command:

```bash
npx skills@latest add https://github.com/mattpocock/skills.git --list
```

If the upstream returns HTTP 502/transient errors, retry conservatively and stop rather than modifying the project with a partial install.

### 3. Conflict analysis

For each of the nine candidates, determine:

- whether an equivalent local skill already exists
- whether the upstream skill changes agent behavior or only provides guidance
- target agent directories/symlinks created by the installer
- whether installation creates duplicate names
- whether existing `.agents` and `.claude` conventions remain authoritative

Prefer integration over replacement.

### 4. Installation strategy

Install only skills that add materially distinct capability.

Do not install all 37 skills.

Do not replace existing custom skills merely because an upstream skill has the same name.

If the CLI's installation model would create a collision, stop and document the conflict instead of forcing it.

### 5. Validation

After any installation:

- inspect `git diff --stat` and `git diff`
- verify no existing skill/rule was silently replaced
- verify symlinks/agent targets are valid
- run the repository's relevant tests/checks
- run `npx skills@latest list`
- update skill indexes/metadata only if the repository's established conventions require it

### 6. Commit boundary

Do not commit automatically unless explicitly requested.

Report:

- installed skills
- skipped skills and why
- files changed
- tests/checks run
- unresolved conflicts
- recommended follow-up

## Acceptance criteria

- Node requirement is satisfied without engine warnings.
- Existing custom skills remain intact.
- No duplicate skill is installed where an equivalent local implementation is authoritative.
- At least the selected non-overlapping candidates are usable by the intended local agent(s).
- Repository skill indexes/configuration accurately reflect the final state.
- Working tree contains only intentional changes.

## Important project context

The project has recently completed G-01 through G-05. Preserve current behavior while performing this integration. Existing project conventions and governance take precedence over generic upstream skill instructions.

In particular, do not weaken deterministic validation behavior, timestamp handling, market-session boundaries, or the distinction between undefined (`None`) and numeric zero metrics.

## Suggested execution order

`baseline audit -> upstream discovery -> overlap matrix -> install non-overlapping skills -> validate -> report`

The local agent should make the smallest safe change that achieves the objective.
