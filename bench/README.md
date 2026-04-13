# SDLC Harness Benchmarks

Canary-based E2E test scenarios for validating the SDLC Harness agent pipeline.

## Structure

```
bench/
├── canaries/          # E2E test scenarios by SDLC phase
│   ├── requirements/  # Requirements generation canaries
│   ├── design/        # Architecture design canaries
│   ├── scaffold/      # Project scaffolding canaries
│   ├── implement/     # Code implementation canaries
│   ├── qa/            # Quality assurance canaries
│   ├── deploy/        # Deployment canaries
│   ├── document/      # Documentation canaries
│   ├── rai/           # Responsible AI canaries
│   └── release/       # Release management canaries
└── results/           # Canary test results (generated)
```

## What Are Canaries?

Canaries are E2E integration tests that validate "does the harness work correctly?"

Each canary spec defines:
- A scenario (input to the harness)
- Expected agent routing and behavior
- Pass/fail criteria based on agent outputs

Canaries test the **harness itself**, not model quality. They feed a scenario into the
agent pipeline and verify the correct agents fire, produce structured output, and meet
evaluation gates.

## Adding a Canary

1. Create a YAML file in `canaries/<phase>/`
2. Define `id`, `phase`, `input`, `expected_outputs`, and evaluation criteria
3. See existing canaries for the schema
