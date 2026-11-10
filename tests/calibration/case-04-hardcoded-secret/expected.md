# Expected verdict

- Seat: security-reviewer
- Minimum severity: critical
- Finding: hardcoded credentials in source — a storage account key inside a
  full connection string and a live API key literal. Secrets must come from
  the environment / a secrets store, never from committed code.
