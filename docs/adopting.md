# Adopting the Harness in Your Organization

The harness ships **one pinned standard per decision point** — that is
what makes its output consistent from engineer to engineer. Adopting it
does not mean finding settings to tune. It means taking ownership of the
standard files the harness deploys into your projects: they start as the
shipped defaults, and from the moment you edit them, the gates enforce
**your** text, not ours.

## Where the standards live

Every surface below lands in your project at workspace initialization
(see [First use](../README.md#first-use)).

| Surface | In your project | What it decides |
|---|---|---|
| Project instructions | `.github/copilot-instructions.md` | Project identity, the stack, and where your organization's templates live |
| Quality instructions | `.github/instructions/` (14 files) | Per-language code and test standards — naming, structure, testing rules the reviewers measure against |
| Reference catalog | `.github/reference-catalog.md` | The approved libraries and patterns for the project |
| Templates | Bundled per stack and type; document templates in `.design/` | The shape of scaffolded projects and of the REQ, ADR, and design documents |
| Manifest patterns | `.SDLC/project-manifest.md` | The patterns recorded for one project, including its approved deviations |
| Cloud pack + MCP config | Chosen at install; `.vscode/mcp.json` | Which vendor rules and MCP servers apply |

## How a change takes effect

Reviewers and gates check work against these texts in a fixed order
(Base Definitions
[§9.2](base-definitions.md#9-precedence-and-resolution--four-chains-four-questions)):
the project's manifest patterns first, then the stack profile's pinned
values and bundled templates, then the reference catalog, then the
language instruction files. Change the text and the next review enforces
your version — there is no settings screen and nothing to recompile.

Two scopes, two places:

- **Organization-wide** — edit the deployed files in your template
  project (or keep your own copies and deploy those at initialization),
  and name your template repository in `copilot-instructions.md`: the
  scaffolder takes templates from there before the bundled ones
  (§9.4).
- **One project only** — record the deviation in that project's
  manifest, with the user's approval. A recorded deviation outranks the
  profile for that project (§9.2); an unrecorded one is just an
  inconsistency the next gate will flag.

Example: your organization requires ProblemDetails error responses from
every API. Add the rule to the code-quality instructions for your APIs'
language (and the approved library to the reference catalog) in your
template project. From then on,
the reviewers measure every API the harness builds against your rule —
and a single project that legitimately cannot comply records a deviation
in its manifest instead of quietly drifting.

## What is not a customization surface

The agents and skills are the process itself — the phases, the gates,
the scoring, the records. They are not settings, and editing a local
plugin copy means your next update overwrites the change. An
organization that needs a different *process* (different phases, a
different QA model) is forking the plugin, and should do it openly, in
its own repository, where the fork is maintained on purpose. Everything
an organization normally needs to make its own — standards, libraries,
templates, stacks — lives in the files above.
