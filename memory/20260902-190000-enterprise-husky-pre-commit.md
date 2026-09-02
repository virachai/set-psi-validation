---
name: enterprise-husky-pre-commit
description: Upgraded .husky/pre-commit to LV99 enterprise-grade determinism gate incorporating uv, ruff, mypy type-checking, and pytest.
metadata:
  type: project
---

**Why:** To ensure strict determinism and enterprise-grade code quality before every commit, catching formatting, linting, type errors, and test failures locally.
**How to apply:**
1. Replaced `.husky/pre-commit` with an LV99 enterprise validation script checking for `uv`, running `ruff check`, `mypy scripts/`, and `pytest`.
2. Removed deprecated Husky v10 wrapper lines (`_.husky.sh`) to prevent warnings and forward-compatibility failures.
3. Verified clean execution and successful pre-commit hook validation across all 111 tests.
