# Expected verdict

- Seat: test-coverage-reviewer
- Minimum severity: critical
- Finding: test integrity violation — with no contract delta in the change,
  one assertion was weakened (`== 201` became `in (200, 201, 500)`, which
  also accepts a server error) and the 422 test was deleted outright. Per
  the base definitions this is `critical` by definition.
