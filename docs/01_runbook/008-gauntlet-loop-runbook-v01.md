# 008-gauntlet-loop-runbook-v01.md

## Purpose

This runbook defines the standard operating procedure for utilizing the `gauntlet-loop` skill to ensure high-fidelity, iterative development for complex tasks within the PSI Validation project.

## When to Use Gauntlet Loop

Use `gauntlet-loop` when a task requires:

1. **High Stakes/Complexity:** Significant architectural changes, complex refactoring, or mission-critical research.
2. **Iterative Refinement:** Tasks where the first attempt is unlikely to be production-ready.
3. **Strict Quality Standards:** Situations requiring adversarial critique to eliminate blind spots, lookahead bias, or structural issues.

## Procedural Workflow

### 1. Define the Goal and Quality Bar

Before activating the skill, clearly define the desired outcome and the criteria for success.

- **Goal:** What is the specific output? (e.g., "Implement a new regime detection algorithm.")
- **Quality Bar:** What are the non-negotiables? (e.g., "Must pass all existing tests, zero lookahead bias, type-hinted, PEP 723 compliant.")

### 2. Activate the Skill

Call `activate_skill(name='gauntlet-loop')`.

### 3. Initiate the Loop

Use one of the following prompts to start:

- `/gauntlet-loop <your goal with success criteria>`
- "Gauntlet this: <goal>"
- "Loop until it beats <bar>"

### 4. Monitor and Guide

The agent will break the task into small, verifiable steps.

1.  **Build:** Implementation of a sub-task.
2.  **Critic:** Adversarial feedback against the established quality bar.
3.  **Refine:** Implementation of corrections.
4.  **Loop:** Continues until the Critic approves the build against the bar.

## Best Practices

- **Be Specific:** The quality bar is the most important part of the prompt.
- **Incremental Validation:** Ensure each sub-step has a clear validation path (e.g., unit test, linter).
- **Do Not Override Early:** Allow the Critic to perform its role; only intervene if the loop stalls or diverges from architectural standards.
