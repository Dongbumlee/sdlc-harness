# syntax=docker/dockerfile:1.7

# Builder stage: resolves dependencies and creates a reproducible virtual environment with uv.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /workspace

COPY pyproject.toml README.md ./
RUN uv lock
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

# Runtime stage: minimal Python image containing only runtime dependencies and source code.
FROM python:3.12-slim-bookworm AS runtime
WORKDIR /workspace
ENV PATH="/workspace/.venv/bin:${PATH}"

COPY --from=builder /workspace/.venv /workspace/.venv
COPY --from=builder /workspace/app /workspace/app
COPY --from=builder /workspace/alembic /workspace/alembic
COPY --from=builder /workspace/alembic.ini /workspace/alembic.ini

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

