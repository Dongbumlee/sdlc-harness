# SDLC Project Manifest

## Scaffolding Summary

- Date: 2026-09-16
- Project: `FeedbackAPI`
- Layer: `API`
- Location: `src/FeedbackAPI`
- Template pattern used: FastAPI API template pattern from `.github/reference-catalog.md` §2.3 (Web API Template) and SDLC scaffolding rules in project instructions.

## Structure Applied

- API code root: `app/`
- Tests root: `tests/`
- Project config: `pyproject.toml` with `[project]` and `uv` workflow
- Containerization: multi-stage `Dockerfile` using `uv sync --frozen`
- CI/CD: per-project `azure_cicd.yaml` with Build/Test/Deploy stages
- Local dev: per-project `.devcontainer/`, `.vscode/`, and project-local `.github/`

## Approved Libraries Included (Reference Catalog)

- `azure-cosmos`
- `azure-storage-blob`
- `azure-identity`
- `pytest-asyncio` (dev/test)

## Notes

- Live template repository verification was not possible because template repository mappings are placeholders in current catalog/instructions.
- Scaffold contains stubs only; business logic and endpoint implementation deferred to Phase 4.

---

## Scaffolding Summary

- Date: 2026-09-16
- Project: `UserManagementAPI`
- Layer: `API`
- Location: `src/UserManagementAPI`
- Template pattern used: FastAPI API template pattern from `.github/reference-catalog.md` §2.3 (Web API Template), adapted to user-management microservice requirements.

## Structure Applied

- API code root: `app/`
- Layered folders: `routers/`, `services/`, `repositories/`, `models/`, `schemas/`
- Core platform folders: `core/`, `middleware/`, `dependencies/`
- Tests root: `tests/`
- Project config: `pyproject.toml` with `[project]` and `uv`
- Containerization: multi-stage `Dockerfile` using `uv sync --frozen`
- Local orchestration: `docker-compose.yml` with app + PostgreSQL + Redis
- Migrations: `alembic.ini` + `alembic/` scaffold
- CI/CD: per-project `azure_cicd.yaml` with Build/Test/Deploy stages
- Dev experience: per-project `.devcontainer/`, `.vscode/`, `.github/workflows/`

## Approved Libraries Included (Reference Catalog + requested stack)

- `fastapi`, `uvicorn`
- `sqlalchemy[asyncio]`, `asyncpg`
- `pydantic-settings`
- `alembic`
- `PyJWT`
- `pytest-asyncio`

## Notes

- GitHub MCP live template probe failed because organization/template repository mappings are placeholders in this workspace.
- awesome-copilot MCP tools were unavailable in this runtime, so Docker/CI best-practice loading could not be executed.
- Scaffold includes architecture and configuration stubs only; production business behavior should be completed in Phase 4.
