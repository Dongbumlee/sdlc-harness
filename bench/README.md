# SDLC Harness Benchmarks

Canary-based E2E test scenarios for validating the SDLC Harness agent pipeline,
plus the frozen evaluation specs every skill carries.

## Structure

```
bench/
├── canaries/          # E2E test scenarios by SDLC phase (60 specs)
│   ├── requirements/  # Requirements generation canaries
│   ├── design/        # Architecture design canaries
│   ├── scaffold/      # Project scaffolding canaries
│   ├── implement/     # Code implementation canaries
│   ├── qa/            # Quality assurance canaries
│   ├── deploy/        # Deployment canaries
│   ├── document/      # Documentation canaries
│   ├── rai/           # Responsible AI canaries
│   ├── release/       # Release preparation canaries (Phase 8)
│   └── publish/       # Publish canaries (Phase 9)
├── evals/             # Frozen per-skill evaluation specs (25) + the
│                      # held-out judgment procedure (evals/README.md)
└── results/           # Canary test results (generated)
```

Specs are validated against the JSON schemas in `schemas/`
(canary specs, cloud packs, skill evaluation specs):

```bash
python tools/validate_canaries.py   # 60 canaries
python tools/validate_evals.py      # 25 eval specs
```

CI runs the same checks: `canary-test.yml` validates canary specs on
PRs touching agents/skills, and `eval-spec-lint.yml` validates the
evaluation specs.

## What Are Canaries?

Canaries are E2E integration tests that validate "does the harness work correctly?"

Each canary spec defines:
- A scenario (input to the harness)
- Expected phase routing and agent behavior
- Pass/fail criteria based on agent outputs

Canaries test the **harness itself**, not model quality. They feed a scenario into the
agent pipeline and verify the correct agents fire, produce structured output, and meet
evaluation gates.

## Adding a Canary

1. Create a YAML file in `canaries/<phase>/`
2. Define `id`, `phase`, `input`, `expected_outputs`, and evaluation criteria
3. See existing canaries for the schema

## Maintaining the sets

Three standing duties keep the sets honest:

- **The ratchet** (base definitions §7): a failure signature that
  fires a pit-stop trigger in a real run becomes a canary or an
  evaluation case, or its run retrospective records why no case
  fits. Field failures are the sets' primary source — a case added
  any other way states what field evidence it stands for.
- **Grader audit** (at each release freeze): graders rot — a
  criterion written against yesterday's failure shape can start
  rejecting correct work. Take a rotating sample of canary specs
  (ten per freeze, cycling through the set), produce a known-good
  response to each in the maintainer's seat, and check the spec's
  graders accept it: keyword and structural criteria mechanically,
  judge criteria by the seat reading the response against them. A
  grader that rejects a known-good response is a spec defect; fix
  it as its own change, with the response kept as the evidence.
  Record the sample and the outcome in the freeze record.
- **Panel tuning** (at each release freeze): the QA panel is itself
  an evaluator, and evaluators drift toward approving their own
  findings away or firing on neighbouring ground. Read the cycle's
  QA reports and run records and note, per reviewer, where it
  over-fired (findings a later phase proved wrong) or under-fired
  (defects a later phase caught that its domain should have caught
  first), each note citing the run record it rests on. A tuning
  finding that indicts a reviewer's description or criteria goes
  through the held-out procedure in `evals/README.md` like any
  behaviour change; the tuning pass itself changes nothing.
