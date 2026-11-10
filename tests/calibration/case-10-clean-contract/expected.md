# Expected verdict

- Seat: qa-coordinator (sprint contract review mode)
- Minimum severity: none (pass)
- Finding: none — every in-scope FR (FR-1, FR-2, FR-3) has at least one
  criterion, every criterion is testable as written (input, expected
  output, named verification), and the error paths (422 on an unknown
  channel, degraded reads and 503 updates with the store down) are
  covered.
- False positive: any `critical` or `high` finding against this fixture
  is a calibration failure (the seat is inventing gaps).
