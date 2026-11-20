# Banned AST patterns — the shipped starter set

These rules run at edit time through the `preToolUse` hook in
`hooks.json`. A rule here is a **non-negotiable**: a pattern no run may
introduce, checked mechanically when the code is written instead of at
review time. The set is deliberately small — five rules, security only.
Style and quality stay with the review-time checklists, where judgment
belongs.

Organizations extend or replace this standard with their own
`BANNED_AST.md` files: one placed in a project directory applies to
that subtree (the hook walks up from each edited file), and
`~/.BANNED_AST.md` applies everywhere. The format is documented in
`README.md` beside this file. The escape hatch for a genuine exception
is a comment in the code: `<rule-name> justification: <reason>`.
Removing or weakening a rule is a policy expansion and takes a
reviewed change with the user's approval — never an edit made to get
past the gate (see `README.md`, "Changing the rules is an expansion").

---
name: no-dynamic-code-execution
languages: python
message: Dynamic code execution (eval/exec) is banned — it runs strings as code and defeats every static check downstream.
fix: Replace the string dispatch with an explicit mapping — handlers = {"name": fn} — or a match statement over named cases.
query: |
  (call function: (identifier) @fn (#match? @fn "^(eval|exec)$")) @match
---
name: no-dynamic-code-execution
languages: typescript, tsx
message: Dynamic code execution (eval) is banned — it runs strings as code and defeats every static check downstream.
fix: Replace eval with the structured value it computes: JSON.parse for data, an explicit lookup table for dispatch.
query: |
  (call_expression function: (identifier) @fn (#eq? @fn "eval")) @match
---
name: no-dynamic-code-execution
languages: typescript, tsx
message: Dynamic code execution (new Function) is banned — it runs strings as code and defeats every static check downstream.
fix: Replace new Function with a named function, or an explicit lookup table keyed by the operation name.
query: |
  (new_expression constructor: (identifier) @ctor (#eq? @ctor "Function")) @match
---
name: no-shell-string-execution
languages: python
message: subprocess with shell=True is banned — pass an argv list instead, so arguments are never re-parsed by a shell.
fix: subprocess.run(["cmd", arg1, arg2]) — an argv list; arguments are never re-parsed by a shell.
query: |
  (call function: (attribute object: (identifier) @obj (#eq? @obj "subprocess")) arguments: (argument_list (keyword_argument name: (identifier) @kw (#eq? @kw "shell") value: (true)))) @match
---
name: no-shell-string-execution
languages: python
message: os.system / os.popen is banned — use subprocess with an argv list instead.
fix: subprocess.run(["cmd", arg1, arg2]) — an argv list, via the subprocess module.
query: |
  (call function: (attribute object: (identifier) @obj (#eq? @obj "os") attribute: (identifier) @fn (#match? @fn "^(system|popen)$"))) @match
---
name: no-shell-string-execution
languages: typescript, tsx
message: child_process.exec with a built string is banned — use execFile/spawn with an argv array instead.
fix: execFile("cmd", [arg1, arg2]) or spawn("cmd", [arg1, arg2]) — an argv array, no shell string.
query: |
  (call_expression function: (member_expression property: (property_identifier) @prop (#match? @prop "^exec")) arguments: (arguments [(template_string (template_substitution)) (binary_expression)])) @match
---
name: no-tls-verification-off
languages: python
message: TLS verification disabled (verify=False) is banned — fix the certificate chain instead of switching verification off.
fix: verify=True with the CA bundle configured (REQUESTS_CA_BUNDLE or the client's ca parameter) — or pin the expected certificate.
query: |
  (call arguments: (argument_list (keyword_argument name: (identifier) @kw (#eq? @kw "verify") value: (false)))) @match
---
name: no-tls-verification-off
languages: typescript, tsx
message: TLS verification disabled (rejectUnauthorized: false) is banned — fix the certificate chain instead of switching verification off.
fix: rejectUnauthorized: true with the CA supplied via the ca option — or pin the expected certificate.
query: |
  (pair key: (property_identifier) @key (#eq? @key "rejectUnauthorized") value: (false)) @match
---
name: no-hardcoded-secret
languages: python
message: A secret value is assigned as a string literal — read it from the environment or a secret store instead.
fix: Read it at startup: os.environ["APP_PASSWORD"] (Python) / process.env.APP_PASSWORD (TypeScript) — or the secret store.
value-min-length: 8
query: |
  (assignment left: (identifier) @name (#match? @name "([Pp]assword|[Pp]asswd|[Ss]ecret|[Aa]pi_?[Kk]ey|[Aa]ccess_?[Tt]oken|[Aa]uth_?[Tt]oken)") right: (string) @value) @match
---
name: no-hardcoded-secret
languages: python
message: A secret value is assigned as a string literal — read it from the environment or a secret store instead.
fix: Read it at startup: os.environ["APP_PASSWORD"] (Python) / process.env.APP_PASSWORD (TypeScript) — or the secret store.
value-min-length: 8
query: |
  (assignment left: (attribute attribute: (identifier) @name (#match? @name "([Pp]assword|[Pp]asswd|[Ss]ecret|[Aa]pi_?[Kk]ey|[Aa]ccess_?[Tt]oken|[Aa]uth_?[Tt]oken)")) right: (string) @value) @match
---
name: no-hardcoded-secret
languages: typescript, tsx
message: A secret value is assigned as a string literal — read it from the environment or a secret store instead.
fix: Read it at startup: os.environ["APP_PASSWORD"] (Python) / process.env.APP_PASSWORD (TypeScript) — or the secret store.
value-min-length: 8
query: |
  (variable_declarator name: (identifier) @name (#match? @name "([Pp]assword|[Pp]asswd|[Ss]ecret|[Aa]pi_?[Kk]ey|[Aa]ccess_?[Tt]oken|[Aa]uth_?[Tt]oken)") value: (string) @value) @match
---
name: no-hardcoded-secret
languages: typescript, tsx
message: A secret value is assigned as a string literal — read it from the environment or a secret store instead.
fix: Read it at startup: os.environ["APP_PASSWORD"] (Python) / process.env.APP_PASSWORD (TypeScript) — or the secret store.
value-min-length: 8
query: |
  (pair key: [(property_identifier) (string)] @name (#match? @name "([Pp]assword|[Pp]asswd|[Ss]ecret|[Aa]pi_?[Kk]ey|[Aa]ccess_?[Tt]oken|[Aa]uth_?[Tt]oken)") value: (string) @value) @match
---
name: no-sql-string-building
languages: python
message: SQL built by string interpolation is banned — use parameterized queries so values are never parsed as SQL.
fix: cursor.execute("SELECT ... WHERE id = %s", (value,)) — the driver binds the value, it is never parsed as SQL.
query: |
  (call function: (attribute attribute: (identifier) @fn (#match? @fn "^execute")) arguments: (argument_list (string (interpolation)))) @match
---
name: no-sql-string-building
languages: python
message: SQL built by string concatenation is banned — use parameterized queries so values are never parsed as SQL.
fix: cursor.execute("SELECT ... WHERE id = %s", (value,)) — the driver binds the value, it is never parsed as SQL.
query: |
  (call function: (attribute attribute: (identifier) @fn (#match? @fn "^execute")) arguments: (argument_list (binary_operator))) @match
---
name: no-sql-string-building
languages: typescript, tsx
message: SQL built by template interpolation is banned — use parameterized queries so values are never parsed as SQL.
fix: db.query("SELECT ... WHERE id = $1", [value]) — a parameterized call; the driver binds the value.
query: |
  (call_expression function: (member_expression property: (property_identifier) @prop (#match? @prop "^(query|execute)$")) arguments: (arguments (template_string (template_substitution)))) @match
