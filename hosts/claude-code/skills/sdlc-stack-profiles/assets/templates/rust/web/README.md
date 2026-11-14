# {{project-name}} web

A server-rendered web app built from the rust/web template
(axum + MiniJinja). The sample slice (an items page with an add
form) is a placeholder — replace it with your own pages; the
delivery guarantees around it are the template.

## The web contract

The browser is untrusted, and the template is shaped by that:

- **Environment split, structurally.** Configuration comes in
  two structs (`src/config.rs`): `PublicConfig` — browser-safe
  values that templates may render — and `ServerConfig` —
  secrets that must never be rendered, logged, or sent to a
  client. Leaking a server secret into a page is this type's
  signature security defect; the test suite pins a sentinel
  secret out of every response while asserting the public values
  do render. Configuration loads through an injected getter, so
  tests supply a fixture map instead of mutating process state.
- **Markup floor (WCAG 2.2 AA).** Every page ships with a
  language attribute, a skip link, landmark regions, exactly one
  `<h1>`, labelled form controls, and visible focus. The page
  tests assert the floor so a new page cannot silently drop it.
- **Post/redirect/get.** Form posts answer 303 to a GET, so a
  refresh never resubmits.
- **Server-rendered first.** Pages render on the server with
  MiniJinja (autoescaping on for `.html`), so rendered values
  are escaped by construction; templates and the stylesheet are
  compiled into the binary.

## Tests

`tests/web_test.rs` drives the router in-process with tower's
oneshot: the items page renders the sample slice, the markup
floor holds, the add-item journey completes, static assets are
served, `/health` answers, and the secret-leak test described
above passes.

## Running

```bash
cargo run --release
```

Configuration is environment-only, prefixed with the tool name
upper-cased (`<PREFIX>_PUBLIC_APP_NAME`, `<PREFIX>_SERVER_API_KEY`),
plus `PORT` (default 8080).

## Development

```bash
cargo test
cargo clippy --all-targets -- -D warnings
cargo fmt --check
```
