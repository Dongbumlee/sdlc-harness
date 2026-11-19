# Skill evaluation specs — and the held-out validation procedure

Each YAML file in this directory is a **frozen** set of cases for one
skill, in two kinds:

- **Trigger cases** — a prompt and whether the skill must fire
  (`skill_invoked: true`) or stay quiet because the prompt belongs to
  a neighbouring skill (`false`). Boundary pairs carry full sets:
  the same prompts appear in both skills' specs with opposite
  expectations, so the boundary itself is what is pinned.
- **Capability cases** — a prompt and strings the output must (or
  must not) contain, taken from values the skill itself pins.

The answer key in a spec derives from the skills' declared scopes.
Once a set is frozen it changes only by a deliberate edit that
records its reason in the change that makes it — moving a key is a
design change, not a fix. `tools/validate_evals.py` lints the specs
(schema and semantics) in CI at zero model cost.

## Judging a behaviour change: the before/after seat pass

Specs alone are inert. What makes them a gate is the procedure a
change goes through before it merges. Any change that alters a
module's **behaviour** — a skill's or agent's instruction text, a
description that drives triggering, a gate rule's wording — is
judged like this:

1. **Pick the set.** The frozen spec for the module's boundary (for
   a skill with no boundary set yet, freeze one first, from the
   declared scopes, as its own change).
2. **Two passes, one seat.** The seat judges every trigger case
   twice: once reading only the *current* text, once reading only
   the *changed* text. Each judgment records the phrase in the text
   that decided it. A pass is written down before scoring, and a
   pass in progress does not re-read the other pass. The default
   seat is a maintainer sitting in the model seat — no live model
   spend. Running the sets on a live model is a separate,
   explicitly opened step; it is not required for this gate.
3. **Score mechanically.** Judgment against the pinned key, no
   judgment calls. The change's PR records the before/after score
   and **every flipped case**, each flip attributed to the specific
   textual difference that caused it.
4. **Verdict.** The change merges when the after-pass shows no
   regression against the key — or when a regression is named in
   the PR and accepted as the stated price of a stated gain. An
   unexplained flip blocks the change: it means the edit does
   something its author did not intend, or cannot explain.

Why this exists: prose accretes. A plausible-sounding rule appended
to a module can silently widen its scope until it swallows a
neighbour's ground — measured on this repository's own QA boundary
set, where a generic rule file dropped a perfect score to 14 of 24,
every error a false trigger on the neighbouring skill's prompts,
and every error traceable to a specific appended rule. The seat
pass is what catches that class of damage before it ships, at the
cost of one careful reading per change.
