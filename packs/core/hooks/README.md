# The edit-time gate (ban-ast layer)

Review-time checklists catch banned patterns after the code exists.
This layer catches a small set of them **at the moment of the edit**:
a Copilot `preToolUse` hook (`hooks.json`) runs `check-bans.mjs` on
every create / edit / apply_patch call, parses the incoming code with
Tree Sitter, and denies the edit when it matches a rule.

## What is banned

The shipped starter set (`BANNED_AST.md` beside this file) holds five
security non-negotiables — dynamic code execution, shell string
execution, disabled TLS verification, hardcoded secrets, and SQL
built by string interpolation/concatenation — for Python and
TypeScript/TSX (JavaScript rides the TypeScript grammar). The set is
deliberately small: this layer is for patterns that may never be
introduced, not for style or general quality, which stay with the
review-time checklists where judgment belongs.

## Rule files

Rules are Tree Sitter queries in `BANNED_AST.md` files. The hook
collects, for each edited file:

1. every `BANNED_AST.md` walking up from the file's directory,
2. `~/.BANNED_AST.md`,
3. the shipped starter set.

A rule block looks like this:

    ---
    name: no-dynamic-code-execution
    languages: python
    message: Shown to the agent when the rule fires.
    query: |
      (call function: (identifier) @fn (#match? @fn "^(eval|exec)$")) @match

`languages` is a comma list of `python`, `typescript`, `tsx`. The
query must name its root capture `@match`; a capture named `@value`
plus a `value-min-length: N` line makes the rule fire only when the
captured string's unquoted length is at least N (the hardcoded-secret
rules use this so short placeholders pass). The same rule name may
appear in several blocks — one per query shape.

## The escape hatch

A genuine exception is recorded in the code itself: a comment
containing `<rule-name> justification: <reason>` on the matched line
or up to three lines above it, inside the edited region, allows that
one match. The justification stays in the code as the record — the
same posture as a manifest deviation.

## Failure posture

A rule match is the only deny. If the gate itself fails — no Node, a
grammar that will not load, an event it cannot parse — it warns on
stderr and allows the edit. A broken gate must not brick every edit,
and the failure is visible rather than silent. Files in languages
without a shipped grammar are not checked by this layer.

## Runtime

Node with the vendored WASM runtime and grammars under `vendor/`
(web-tree-sitter; grammars for Python, TypeScript, TSX). No install
step and no native builds. Host scope today: the Copilot hook
contract; other hosts map their own hook contract onto the same
checker.
