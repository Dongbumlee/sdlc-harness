# User Management API

This project is a FastAPI scaffold for a user-management microservice.

## Purpose

- Provide a production-ready starting structure with clear API/service/repository separation.
- Include async SQLAlchemy + PostgreSQL wiring, JWT token scaffolding, and Alembic migration setup.
- Support local development with Docker Compose and quality tooling.

## Quick start

1. Copy environment settings:
   - `cp .env.example .env`
2. Install dependencies:
   - `uv sync`
3. Run the API:
   - `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Project layout

- `app/routers/`: API endpoints and HTTP handlers.
- `app/services/`: orchestration layer (business flow stubs).
- `app/repositories/`: data access layer.
- `app/models/`: SQLAlchemy ORM entities.
- `app/schemas/`: Pydantic request/response models.
- `alembic/`: migration configuration and revisions.

