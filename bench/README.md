# SDLC Harness Benchmarks

Canary-based evaluation framework for measuring Copilot agent quality across SDLC phases.

## Structure

```
bench/
├── canaries/          # Test scenarios by SDLC phase
│   ├── requirements/  # Requirements generation canaries
│   ├── implement/     # Code implementation canaries
│   ├── qa/            # Quality assurance canaries
│   ├── design/        # Architecture design canaries
│   ├── deploy/        # Deployment canaries
│   ├── document/      # Documentation canaries
│   ├── scaffold/      # Project scaffolding canaries
│   ├── rai/           # Responsible AI canaries
│   └── release/       # Release management canaries
├── graders/           # Evaluation components
│   ├── code/          # Deterministic graders (AST, keyword, file, structural)
│   └── llm/           # LLM-based graders (judge, consensus, rubric)
├── engine/            # Scoring, trend analysis, report generation
└── reports/           # Historical benchmark reports + baseline
```

## Quick Start

```bash
# Run all benchmarks
python tools/run-benchmarks.py

# Run a specific phase
python tools/run-benchmarks.py --phase requirements

# Run a specific canary
python tools/run-benchmarks.py --canary req-001-ecommerce-api

# Compare against baseline
python tools/run-benchmarks.py --compare-baseline
```

## Adding a Canary

1. Create a YAML file in `canaries/<phase>/`
2. Define `id`, `phase`, `input`, `expected_outputs`, and `graders`
3. See existing canaries for the schema

## Grader Types

| Type | Module | Use Case |
|------|--------|----------|
| KeywordGrader | `bench.graders.code.keyword_grader` | Check for required terms |
| ASTGrader | `bench.graders.code.ast_grader` | Validate code structure |
| StructuralGrader | `bench.graders.code.structural_grader` | Check architectural patterns |
| FileGrader | `bench.graders.code.file_grader` | Validate file outputs |
| JudgeGrader | `bench.graders.llm.judge_grader` | LLM quality judgment |
| ConsensusGrader | `bench.graders.llm.consensus_grader` | Multi-LLM agreement |
| RubricGrader | `bench.graders.llm.rubric_grader` | Rubric-based LLM scoring |
