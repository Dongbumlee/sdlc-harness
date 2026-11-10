# Expected verdict

- Seat: code-quality-reviewer
- Minimum severity: high
- Finding: mutable default argument (`active: list[str] = []`) — the default
  list is shared across calls, so filters leak between unrelated requests
  for the lifetime of the process. A correctness defect, not a style note.
