FROM mcr.microsoft.com/azurelinux/base/python:3.12

WORKDIR /app

# Install uv from the official image (never pip install uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy and install dependencies
COPY . /app
RUN uv sync --frozen --no-cache

# Run as a non-root user on an unprivileged port — the same posture
# as every other bundled template.
# The Azure Linux base image does not ship the account tools
# (groupadd/useradd live in shadow-utils), so install them first.
RUN tdnf install -y shadow-utils && tdnf clean all \
    && groupadd --system app && useradd --system --gid app app \
    && chown -R app:app /app
USER app
EXPOSE 8080

# Run the application
CMD [".venv/bin/uvicorn", "app.main:app", "--port", "8080", "--host", "0.0.0.0", "--workers", "1"]
