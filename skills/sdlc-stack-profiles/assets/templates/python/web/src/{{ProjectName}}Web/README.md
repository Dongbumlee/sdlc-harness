# {{project-name}} web app

Server-rendered web app (FastAPI + Jinja2). See the template-level
README for the web contract this project follows.

## Development

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8080
uv run pytest
```
