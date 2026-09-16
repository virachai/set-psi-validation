# RFC 012: Community Standards Adoption (v01)

## 🎯 Objective

This RFC proposes the adoption of industry-standard community files and governance templates to ensure the project is professional, legally clear, and ready for collaboration.

---

## 1. Legal Clarity (License)

- **Status**: Done
- **Problem**: The project currently lacks a license, making its legal status ambiguous for potential users and contributors.
- **Proposed Solution**:
  - Adopt the **MIT License**. It is permissive, well-understood, and suitable for quantitative research tools.
  - Create a `LICENSE` file in the root directory.

---

## 2. Contribution Guidelines

- **Status**: Done
- **Problem**: There is no guide for how to contribute to the "Truth Layer", which has strict engineering requirements (e.g., no lookahead bias).
- **Proposed Solution**:
  - Create `CONTRIBUTING.md`.
  - Document the setup process, coding standards (ruff/mypy/pytest), and the critical requirement of respecting the SET market schedule.

---

## 3. Governance & Safety

- **Status**: Done
- **Problem**: No Code of Conduct or Security Policy exists to govern interactions or report vulnerabilities.
- **Proposed Solution**:
  - Create `CODE_OF_CONDUCT.md` using the Contributor Covenant v2.1.
  - Create `SECURITY.md` to provide a clear path for reporting security issues (e.g., potential data integrity leaks or API key exposure risks).

---

## 4. GitHub Operational Templates

- **Status**: Done
- **Problem**: Issues and Pull Requests currently lack structure, leading to inconsistent reports and reviews.
- **Proposed Solution**:
  - Create `.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`.
  - Create `.github/PULL_REQUEST_TEMPLATE.md` to ensure every PR includes verification steps and impact assessment.

---

**Effective Date**: 2026-06-16  
**Governance**: Compliant with "Lean PSI Validator" principles (Actionable, Measurable, Standardized).
