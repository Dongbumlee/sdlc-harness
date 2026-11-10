# Expected verdict

- Seat: architecture-reviewer
- Minimum severity: high
- Finding: dependency direction inverted — a service imports from the
  routers layer (`app.routers.reports`). Services sit below routers in the
  recorded layering; the service must not depend on the HTTP layer's route
  definitions.
