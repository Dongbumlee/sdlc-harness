# Reviewer calibration corpus

Known-answer fixtures for the QA panel seats. Every case plants (or
deliberately does not plant) a defect with a recorded expected verdict, so
a reviewer definition can be scored instead of argued about.

## Cases

| Case | Seat | Expected |
|---|---|---|
| case-01-clean | any | Pass — any `critical`/`high` finding is a false positive |
| case-02-off-by-one | code-quality | `high`+ correctness finding (1-based page treated as 0-based) |
| case-03-mutable-default | code-quality | `high`+ correctness finding (mutable default argument) |
| case-04-hardcoded-secret | security | `critical` (credentials committed in source) |
| case-05-layering-violation | architecture | `high`+ (service imports the routers layer) |
| case-06-test-weakening | test-coverage | `critical` by definition (assertion weakened, test deleted, no contract delta) |
| case-07-untestable-requirement | requirements-completeness | `high`+ (no acceptance criteria; unmeasurable NFR language) |

## How to run

1. Pick a case and a seat. The runner sits in the seat: read the seat's
   agent definition in full, then review only the case's `input/` tree and
   emit the seat's normal YAML review block.
2. Score against `expected.md`:
   - **Hit** — the expected finding appears at or above the minimum
     severity.
   - **Miss** — the finding is absent, or recorded below the minimum
     severity.
   - **False positive** — a `critical`/`high` finding the expected file
     does not sanction (case-01 fails on any of them).
3. Record the run: date, seat definitions at which commit, per-case
   hit/miss, and the verbatim YAML blocks. A miss is a definition defect
   first and a seat failure second — check whether the seat's checklist
   even has a lens for the planted defect before blaming the run.

## When to re-run

- Any change to a reviewer agent definition, the reviewer output format,
  or the QA Coordinator's synthesis rules.
- Before drawing conclusions about a new model generation in a judgment
  seat — this corpus is the instrument that turns "the cheap seat seems
  fine" into a measurement.
