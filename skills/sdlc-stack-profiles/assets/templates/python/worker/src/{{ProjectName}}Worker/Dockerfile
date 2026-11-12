FROM mcr.microsoft.com/azurelinux/base/python:3.12

WORKDIR /app

# Install uv from the official image (never pip install uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy and install dependencies
COPY . /app
RUN uv sync --frozen --no-cache

# Run as a non-root user — the same posture as every other bundled
# template. The job database lives on a mounted volume in production
# (the <PREFIX>_DB_PATH variable points at it, where the prefix is
# the upper-cased tool name); the default path is for local runs.
RUN groupadd --system app && useradd --system --gid app app && chown -R app:app /app
USER app

# SIGTERM is the shutdown contract: the runner finishes the current
# job and exits; a job stranded anyway returns through its lease.
CMD [".venv/bin/python", "-m", "app"]
