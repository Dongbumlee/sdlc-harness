# Agent Harness Design

The QA system draws from [Anthropic's research on harness design
for long-running applications](https://www.anthropic.com/engineering/harness-design-long-running-apps),
which found that separating the generator from the evaluator — and tuning the evaluator
to be skeptical — dramatically improves output quality.

## Key patterns applied across the full SDLC

| Pattern | What the research found | How we apply it |
|---|---|---|
| **Generator-evaluator separation** | Agents asked to evaluate their own work are inherently lenient — they identify real issues then talk themselves into approving anyway. | 9 independent QA reviewers run in parallel, each in its own context window. None sees what the others found. |
| **Adversarial QA posture** | Out-of-the-box LLM QA agents test superficially and skip edge cases. | Every reviewer has explicit anti-leniency instructions: _"Do NOT be generous. Do NOT downgrade findings."_ |
| **Numeric scoring with hard thresholds** | Vague categories ("looks good") enable drift. Concrete scores create accountability. | Each reviewer scores 1-10. Security requires ≥8. Any Critical finding = automatic fail. Composite < 7 = fail. |
| **Iterative feedback loops** | A single-pass review that identifies issues but never verifies fixes leaves quality gaps. | Every phase transition is an evaluation point. QA uses scored re-review loops. All phases validate before handoff. |
| **Planner scope control** | Over-specifying implementation upfront leads to cascading errors. Under-specifying means the generator drifts. | The Analyst focuses on deliverables and constraints, not implementation details. The Implementer defines testable acceptance criteria before coding. |
| **Self-evaluation before handoff** | Generators are overly positive about their own work. | ALL generator agents (Analyst, Scaffolder, Deployer, Implementer, Documenter) run domain-specific self-evaluation checklists before reporting complete. |

## Self-evaluation per agent

| Agent | Self-evaluation | Acceptance criteria | Feedback loop |
|---|---|---|---|
| **Analyst** | Design completeness, testability, scope control, NFR coverage | — (produces criteria for others) | Design revision loop via Harness |
| **Scaffolder** | Template fidelity, file existence, dependency correctness | Required files checklist | Structure validation via Harness |
| **Deployer** | AVM versions, compilation, no hardcoded values, diagnostics | Infrastructure quality checklist | Bicep fix loop via Harness |
| **Implementer** | Acceptance criteria coverage table | Sprint contract before coding | QA re-review loop (up to 3 rounds) |
| **Documenter** | Template compliance, code accuracy, no placeholders, link integrity | — | Revision loop via Harness |
| **QA Reviewers** | — (they ARE the evaluators) | — | Adversarial scoring with thresholds |

## Evaluation gates

- **Weighted scoring**: Security × 1.5, others × 1.0 → composite = `(security × 1.5 + sum of other active domains) / (1.5 + active domains)` — 9.5 is only the full-panel denominator.
- **Hard-fail rules**: composite < 7, security < 8, any domain < 5, any Critical finding, or two or more Important findings within a single reviewer domain
- **3-tier escalation**: auto-retry → targeted retry → user decision; round caps scale with the task grade (Phase 6: Small 2, Medium 3, Large 3)
- **Phase-specific routing**: not all phases need all 9 reviewers

## Structured reviewer output

All 9 QA reviewers emit structured YAML between delimiters:

```yaml
---sdlc-review-output---
reviewer: "<agent-name>"
status: complete | partial
score: <1-10>
verdict: PASS | FAIL | CRITICAL_FAIL
findings:
  - severity: critical | high | medium | low
    category: <domain-specific>
    description: "<finding>"
    location: "<file:line>"
    recommendation: "<fix>"
    scope: in-scope | out-of-scope
    requirement: "<acceptance criterion or recorded standard>"
not_checked:
  - "<area not covered, and why>"
reasoning: "<evaluation summary>"
---end-sdlc-review-output---
```

Every finding carries a `severity`, a `scope`, and the `requirement` it is
measured against; every block carries `status` and `not_checked` — see
`docs/base-definitions.md` §4 for the canonical contract and the severity
translation table (finding levels ↔ synthesis terms).
