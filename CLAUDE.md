# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

We're building the project described in @SPEC.md. Read that file for general architectural tasks or to double-check the exact database structure, tech stackor application architecture.

A clean, minimal **FastAPI + PostgreSQL + Alembic** backend template. It ships the database/session/config plumbing, Alembic migrations (with the `pgvector` extension enabled by the base migration), a Docker Compose stack (api + postgres + adminer), and health/readiness endpoints — but **no application tables or domain models yet**. It is a starting point: add your own SQLAlchemy models, Pydantic schemas, and routers on top.

Whenever working with any third-party library or something similar, you MUST look up the official documentation to ensure that you're working with up-to-date information.

Use the DocsExplorer subagent for efficient documentation lookup.
Note: the codebase was reset from a prior finance app. Some infra names still carry that history (Docker `container_name`s are `finance_backend_api`/`_db`/`_adminer`; `models.py` mentions removed `WatchlistItem`/`FinanceNote` tables). Nothing depends on the `finance` naming.

## Commands

The `Makefile` targets run on the **host** (they need local Python/Postgres and `SQLALCHEMY_DATABASE_URL` pointing at `localhost`):

- `make install` — install runtime + dev deps (`pip install -r requirements.txt`)
- `make dev` — run the API locally with autoreload (`uvicorn main:app --app-dir src --reload`)
- `make test` — run the full pytest suite
- `make fmt` — format with black (`black src alembic tests`)
- `make migrate` — `alembic upgrade head`
- `make revision m="msg"` — autogenerate a migration
- `make up` / `make down` / `make logs` — full Docker stack (api + postgres + adminer)

Run a single test: `pytest tests/test_health.py::test_health_readiness`.

The README treats **Docker Compose as the source of truth** for running the app; host-based runs are possible (via the Makefile) but not the documented path. To run anything inside the container instead, use `docker compose run --rm api <cmd>` — e.g. `docker compose run --rm api pytest` or `docker compose run --rm api alembic upgrade head`. This works because dev/test tools ship in the same image (see below).

There is no linter or type-checker configured — `black` is the only style tool.

## Critical: flat-import layout

The app runs with `--app-dir src`, so `src/` is the import root and **all imports inside `src/` are flat/top-level**, not package-relative: `from routers import ...`, `from database import Base`, `from deps import db_dependency`. There is no `src` package prefix, and `routers/__init__.py` is empty (no re-exports). New modules must follow this convention or imports break.

This is also why:

- `pytest.ini` sets `pythonpath = src` so tests can `from main import app`.
- `alembic.ini` sets `prepend_sys_path = src`, so `alembic/env.py`'s bare `import models` resolves when Alembic is invoked from the repo root. For ad-hoc alembic runs from elsewhere, ensure `src` is importable.

## Architecture

Request flow: `main.py` creates the app and includes the health router → routers depend on shared helpers in `deps.py` → `database.py` provides the session → PostgreSQL.

- **`src/main.py`** — creates `app` and includes the `health` router. Nothing else is wired yet.
- **`src/models.py`** — re-exports the SQLAlchemy declarative `Base` (from `database`). **No application tables are defined yet**; add ORM models here. `models.Base` must stay importable because Alembic's `env.py` uses `models.Base.metadata` and the tests `import models` to register tables.
- **`src/schemas.py`** — Pydantic v2 request/response models. Currently empty; add schemas as endpoints are built.
- **`src/deps.py`** — shared dependencies for reuse by future routers: `db_dependency` (injected `Session`), `get_or_404(db, Model, item_id, detail)`, and `Pagination`/`PaginationParams` (`?limit=&offset=`, defaults limit 50, max 200).
- **`src/database.py`** — `engine` / `SessionLocal` / `Base` and the `get_db` generator dependency.
- **`src/config.py`** — `pydantic-settings` `Settings`; the only setting is `sqlalchemy_database_url` (env var `SQLALCHEMY_DATABASE_URL`, loaded from `.env` if present). Add new config as typed fields here.

### Routers

- **`src/routers/health.py`** — `GET /health` (liveness; returns `{"status": "ok"}`, does not touch the DB) and `GET /health/ready` (readiness; runs `SELECT 1` via `db_dependency`, returns 503 if the DB is unreachable). Both work with zero application tables.

## Database & migrations

- Migrations live in `alembic/versions/`. `env.py` reads the DB URL from `SQLALCHEMY_DATABASE_URL` (falling back to `alembic.ini`'s empty `sqlalchemy.url`, and raising if neither is set), and uses `models.Base.metadata` as the autogenerate target.
- There is a single **base migration** `c3e7f1a2b4d6` (`down_revision = None`) whose only job is `CREATE EXTENSION IF NOT EXISTS vector;`. The `pgvector` extension is provisioned ahead of future semantic-search work; no vector column exists yet. The Docker DB image is `pgvector/pgvector:pg16`. New migrations should chain off this base.
- In Docker, `entrypoint.sh` waits for Postgres, runs `alembic upgrade head`, then starts uvicorn — migrations are applied automatically on container start.

## Testing

`tests/conftest.py` provides a `client` fixture: a fresh **in-memory SQLite** DB per test (via `StaticPool`), with `get_db` overridden through `app.dependency_overrides`. No running Postgres is needed for tests. `tests/test_health.py` covers `/health` and `/health/ready` (the readiness `SELECT 1` runs fine against SQLite too). Be aware that Postgres-specific behavior (including `pgvector`) is not exercised by these SQLite tests.

## Configuration

Copy `.env.example` → `.env` (gitignored). Key vars: `SQLALCHEMY_DATABASE_URL` (host `db` inside Docker, `localhost` for host-based runs), Postgres credentials (`POSTGRES_USER`/`_PASSWORD`/`_DB`), and the published host ports (`API_PORT`, `POSTGRES_PORT`, `ADMINER_PORT`). All dependencies — runtime plus dev/test tools (`pytest`, `pytest-asyncio`, `black`) — live in a single `requirements.txt`, so they are present in the Docker image too (this is what lets `docker compose run --rm api pytest` work).

## Adding a feature

Add ORM models to `src/models.py`, schemas to `src/schemas.py`, a router under `src/routers/` (and `app.include_router(...)` it in `src/main.py`), then autogenerate a migration that chains off the `pgvector` base. Keep imports flat (see above).
