# Security Policy

## Supported Versions

We provide security updates for the following versions of **SET PSI Validation**:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ Yes             |
| < 0.1.0 | ❌ No              |

## Reporting a Vulnerability

We take the security of our quantitative research tools seriously. If you discover a security vulnerability—especially those related to **data integrity leaks**, **lookahead bias exploits**, or **API key exposure**—please follow these steps:

1.  **Do Not Open a Public Issue:** To prevent exploitation, please report vulnerabilities privately.
2.  **Contact:** Reach out to the maintainers via the contact information provided in the repository profile or project documentation.
3.  **Details:** Include a detailed description of the vulnerability, steps to reproduce, and the potential impact on validation metrics.

We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Scope

This policy covers all code in this repository, including:
* Market data capture scripts (`scripts/python/capture_market.py`)
* Validation logic (`scripts/python/validation_engine.py`)
* Environment configuration templates (`.env.example`)

---

**Note:** As this is a research tool, users are responsible for securing their own local `.env` files and API credentials. Never commit secrets to the repository.
