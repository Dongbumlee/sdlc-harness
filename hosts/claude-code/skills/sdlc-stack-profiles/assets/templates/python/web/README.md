# {{project-name}} web

A server-rendered web app built from the python/web template.
The sample slice (an items page with an add form) is a
placeholder — replace it with your own pages; the delivery
guarantees around it are the template.

## The web contract

The browser is untrusted, and the template is shaped by that:

- **Environment split, structurally.** Configuration comes in
  two kinds that live in two different objects
  (`app/config.py`): `PublicConfig` — browser-safe values that
  templates may render — and `ServerConfig` — secrets that must
  never be rendered, logged, or sent to a client. Leaking a
  server secret into a page is this type's signature security
  defect; the test suite pins a sentinel secret out of every
  response while asserting the public values do render.
- **Markup floor (WCAG 2.2 AA).** Every page ships with a
  language attribute, a skip link, landmark regions, exactly one
  `<h1>`, labelled form controls, and visible focus. The page
  tests assert the floor so a new page cannot silently drop it.
- **Post/redirect/get.** Form posts answer 303 to a GET, so a
  refresh never resubmits.
- **Server-rendered first.** Pages render on the server from the
  same service layer an API would use; client scripts enhance,
  they are not the only path to the content.

## Tests

`tests/test_web.py` drives the app over HTTP with FastAPI's
TestClient: the items page renders the sample slice, the markup
floor holds, the add-item journey completes, static assets are
served, `/health` answers, and the secret-leak test described
above passes.

## Running

```bash
uv sync
uv run uvicorn app.main:app --port 8080
```

Configuration is environment-only, prefixed with the tool name
upper-cased (`<PREFIX>_PUBLIC_APP_NAME`, `<PREFIX>_SERVER_API_KEY`).

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
