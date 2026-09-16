# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /workspace

COPY pyproject.toml README.md ./
RUN uv lock
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

COPY app ./app
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /workspace
ENV PATH="/workspace/.venv/bin:${PATH}"

COPY --from=build /workspace/.venv /workspace/.venv
COPY --from=build /workspace/app /workspace/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

