# Security Policy

## Reporting a vulnerability

Report vulnerabilities privately to the maintainers — use GitHub's
private vulnerability reporting on this repository (Security →
Report a vulnerability) rather than a public issue. Please include
the affected component (agent, skill, tool script, or template),
reproduction steps, and the impact you observed.

Do not open public issues for active vulnerabilities.

## Scope notes

SDLC Harness is agent definitions, skills, and tooling scripts that
run inside your own Copilot client, under your own accounts:

- The harness executes no hosted code and holds no credentials of
  its own. Agents act through your client's tools, under your
  permissions and approvals.
- Reports about prompt-level behavior (an agent instruction that
  could be abused — for example, instructions that talk a seat into
  skipping a gate or leaking context) are in scope and welcome.
- Vulnerabilities in bundled project templates (for example, an
  insecure default in a scaffolded app) are in scope; report them
  against the template, not the generated project.
