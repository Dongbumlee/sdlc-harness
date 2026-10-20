# ADR-0003: GitHub-Native Operations — Repository First, Work Tracked in Issues/PRs, Test Evidence from CI

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** Dongbum Lee (product owner), Cindy (harness maintainer)
- **Related:** ADR-0002 (bundled default templates), manifest Phase-State Ledger, QA evidence pack

## Context

The 2026-10-19 baseline end-to-end run (bundled `dotnet/api` template, all nine
phases completed on a clean greenfield project) exposed four gaps that prose
instructions alone did not close:

1. **No LICENSE shipped.** The Scaffolder's compliance checklist already lists
   `LICENSE` as a required root file, but no bundled template contains one, so
   the scaffolded project finished without it. A checklist line is not a file.
2. **The repository arrived last.** The project was not a git repository until
   the release phase created a local one. Nothing was pushed; publication was
   left as an end-of-run human decision instead of being the medium the work
   happened in from the start.
3. **Work was invisible outside the session.** Phase progress existed only in
   the local manifest ledger and the session transcript. A human (or another
   agent) could not follow what was happening, review increments, or pick up a
   stalled item from GitHub.
4. **Test evidence was self-recorded.** QA reviewers in the Copilot CLI
   surface have no shell, so test verification rested on locally recorded
   output ("verified (recorded; not re-run)"). The run's own test log was the
   only evidence the gate consumed.

## Decision

### D1. MIT LICENSE ships inside every bundled template

Each bundled template (ADR-0002) carries a `LICENSE` file at its root with the
standard MIT text. The copyright line uses two existing-style tokens:
`Copyright (c) {{Year}} {{ProjectName}} contributors`. `{{Year}}` is added to
the template token contract (declared in each `template.yaml`, substituted at
instantiation with the current year). An organization template or an explicit
user decision overrides the license; the chosen license is recorded in the
manifest next to the template provenance. The same treatment (a real file in
the template, not a checklist line) is the pattern for any future compliance
file.

### D2. The repository is created first, private by default — behind a mandatory intake gate

Initialization includes a **mandatory GitHub intake**; the run does not
reach scaffolding until it is complete or explicitly waived by the user:

1. **Verify authentication.** The Harness checks who is signed in to GitHub
   (GitHub MCP `get_me`, fallback `gh auth status`) and records the account
   login. If GitHub is not authenticated, the run stops and asks the user to
   authenticate — or to explicitly choose local-only mode. No silent
   assumption.
2. **Ask the repository questions once, at intake:** create new / use
   existing / local-only; for a new repository — name (default: the project
   name), owner (default: the authenticated account), visibility **private**
   (default). The questions must actually be asked — wording inside the
   task prompt (e.g. "build in this empty repository") is never an answer
   and must never be recorded as a user decision; the manifest records the
   decision source alongside the mode. (Clarified 2026-10-19 after the
   first simulation inferred local-only from the feature prompt's prose.)
3. **Create the repository at intake** (GitHub MCP `create_repository` where
   available, otherwise `gh repo create`), and record the intake in the
   manifest (`github_account`, `repository_mode`, URL, visibility, default
   branch; the manifest skeleton is created at intake if needed). The
   scaffold is pushed as the first commit.

If GitHub is unavailable or the user declines, the run proceeds local-only,
records that in the manifest, and the Release Manager performs the repository
creation as a catch-up step before release (warn-and-proceed, consistent with
the existing GitHub MCP policy). Creating a private repository is never a
mid-run surprise: it is an intake decision, defaulted to private.

### D3. A pull request template ships inside every bundled template

Each bundled template carries `.github/pull_request_template.md`, using the
structure most widely recommended in current open-source practice
(summary / type of change / how it was tested / checklist / linked issues).
Harness-opened PRs are expected to fill it in; the checklist includes the
harness-specific items (tests run, manifest ledger updated, ADR if a decision
changed).

### D4. Agents actively work in GitHub Issues and PRs — it is the working medium, not a log

The orchestrator and every subagent use GitHub as the place work happens,
not as an after-the-fact record. This matters mechanically: in the Copilot
CLI surface, subagents reliably receive MCP tools even when their shell and
file access are limited (measured in the baseline run: MCP servers were the
one channel that reached every reviewer). GitHub MCP therefore gives agents
capabilities the local surface denied them — PR diffs instead of guessed
file paths, code search instead of file-by-file browsing, Actions logs
instead of recorded summaries.

Per-role expectations:

- **Harness (orchestrator):** opens the phase Issue when a phase starts,
  links the work, watches the relevant Actions runs for gate evidence, and
  closes the Issue when the Phase-State Ledger marks the phase Complete.
- **Implementer:** opens a draft PR early and pushes incrementally; a red
  CI run is its own feedback — read the failed check's log via GitHub MCP,
  fix, push again — not a surprise discovered at QA time.
- **Reviewers:** read the PR diff and search the code via GitHub MCP
  instead of guessing local paths; findings that need follow-up become PR
  review comments or Issues, attached to the code they describe.
- **QA Coordinator:** the gate decision cites check-run conclusions read
  from GitHub, never a subagent's self-declared summary.
- **Release Manager:** creates the tag and release on GitHub; release notes
  are drawn from the merged PRs.

Structure underneath the activity:

- One Issue per phase (or per work package within a phase), labeled
  `sdlc:phase-<n>`. All changes land through PRs that reference their Issue
  (`Closes #<n>`).
- **The manifest Phase-State Ledger remains the local source of truth** for
  resume-after-interruption. Synchronization is one-directional,
  ledger → GitHub, so the two never conflict. If GitHub is unavailable, work
  proceeds locally and the pending sync is noted in the ledger.

### D5. Test evidence for gates comes from CI

- Bundled templates' GitHub Actions workflows run the profile's test command
  on every PR and on pushes to the default branch.
- Implementers still run tests locally during development (fast feedback).
- The Phase 6 evidence pack records the **CI run for the commit under
  review** (check-run conclusion and URL, read via GitHub MCP) as the gate's
  test evidence; the QA report cites that run. Locally recorded output
  (`qa-evidence/test-run.txt`) remains the fallback when no CI run exists,
  and the QA report states that limitation explicitly when it applies —
  the same honesty rule as the recorded-not-re-run pattern it replaces.

## Consequences

- A fresh project is reviewable from its first hour: code, issues, PRs, and
  CI results are where a human already looks.
- The QA gate's central evidence becomes independently checkable by any
  reviewer (human or agent) with GitHub read access — no shell required.
- The release phase stops being a repository-creation event and becomes what
  it should be: versioning and publishing an already-tracked history.
- Cost/dependency: private-repository Actions minutes are consumed per run
  (within the GitHub Free/Pro included minutes at this project's scale), and
  D2/D4/D5 degrade to local-only when GitHub is unavailable — by design, with
  the degradation recorded rather than silent.

## Implementation checklist

- [x] `LICENSE` (MIT) in all three bundled templates; `{{Year}}` token added
      to each `template.yaml`; `tools/verify_templates.py` passes.
- [x] `.github/pull_request_template.md` in all three bundled templates.
- [x] Scaffolder: instantiation notes cover `{{Year}}` substitution and the
      license-override rule; compliance checklist cites the template files.
- [x] Harness: repository bootstrap step at Phase 3 entry (intake questions,
      create + first push, manifest `repository` record); one-directional
      ledger → Issue sync rule in the phase-transition steps.
- [x] QA evidence collector + QA Coordinator: cite the CI check-run for the
      reviewed commit; local fallback labeling.
- [x] Release Manager: repository catch-up path for local-only runs; publish
      gate assumes the remote exists.
- [x] Repo self-checks green: `pytest`, `assemble_flat_layout.py --check`,
      pack contracts, template verification.
- [ ] Exercised by a fresh greenfield E2E run on the test box before merge.
