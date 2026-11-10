# Expected verdict

- Seat: qa-coordinator (sprint contract review mode)
- Minimum severity: critical
- Finding: FR-3 has no criterion. The contract covers the happy paths
  (FR-1, FR-2, and an empty-set edge) but says nothing about a record
  that fails serialization — the skip-and-report behavior FR-3 requires
  is unverifiable as written. In contract-review mode a coverage gap on
  an in-scope FR is a critical gap: it goes back to the Implementer
  before code exists.
- False positive: findings against FR-1/FR-2 coverage or criterion
  testability — both are covered, with named verification.
