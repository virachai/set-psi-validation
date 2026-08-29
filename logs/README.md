# Logs Directory

Runtime logs captured by the application and background processes.

## Files

- `app.jsonl` – JSON Lines log stream for the main service.

## Rotation & Retention

- Logs are rotated daily; older files are compressed and stored in `logs/archived/` (created automatically).
- Retention policy: keep 30 days of raw logs, then purge.

> **Note**: Do not edit log files manually. Use the provided monitoring tools to query logs.
