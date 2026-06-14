# scripts

## Purpose
Executable utilities for environment management, data orchestration, and governance automation.

## Function
This directory provides the operational tooling required to maintain the Chronos ecosystem. It handles tasks that are outside the scope of core application logic, such as infrastructure provisioning, data synchronization, and forensic auditing.

## Never-Implement Mandate
**CRITICAL**: Scripts in this directory MUST NOT contain core application logic, signal generation algorithms, or trading strategies. These are reserved for the specialized service repositories. Scripts are strictly for:
- Environment setup and configuration.
- Data ingestion and transformation (ETL).
- CI/CD pipelines and deployment automation.
- Administrative and governance tasks.

## Naming Convention
- Shell Scripts: `snake_case.sh`
- Python Utilities: `snake_case.py`
- Configuration Templates: `kebab-case.env.example`
