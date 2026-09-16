# Common development commands for local workflows.

.PHONY: sync run lint test format migrate revision up down compose-up compose-down

sync:
	uv sync

run:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	uv run ruff check app tests

format:
	uv run ruff check app tests --fix

test:
	uv run pytest -q

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "init"

up:
	uv run alembic upgrade head

down:
	uv run alembic downgrade -1

compose-up:
	docker compose up --build

compose-down:
	docker compose down -v

