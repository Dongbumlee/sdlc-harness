FROM mcr.microsoft.com/azurelinux/base/python:3.12

WORKDIR /app

# Install uv from the official image (never pip install uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy and install dependencies
COPY . /app
RUN uv sync --frozen --no-cache

# Run the application
CMD [".venv/bin/uvicorn", "app.main:app", "--port", "80", "--host", "0.0.0.0", "--workers", "4"]
