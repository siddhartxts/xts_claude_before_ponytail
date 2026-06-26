# FastAPI + PostgreSQL + Alembic Backend Template

A clean, minimal backend template: **FastAPI** for the API, **PostgreSQL** (with the
`pgvector` extension) for storage, and **Alembic** for schema migrations. The whole
stack runs through Docker Compose, and a browser-based database UI (Adminer) is
included for inspecting the data.

It is intentionally a **starting point, not a finished app**: there are currently
**no application tables** and no domain models. You get the plumbing — config,
database session, migrations, Docker, and health/readiness endpoints — ready to build
on. Add your own SQLAlchemy models, Pydantic schemas, and routers on top.

## Tech stack

- **FastAPI** — web framework / REST API
- **PostgreSQL** (`pgvector/pgvector:pg16`) — database, with `pgvector` enabled
- **SQLAlchemy** — ORM / session management
- **Alembic** — database migrations
- **Docker Compose** — runs the entire stack
- **Adminer** — browser-based database UI
- **Pytest** — test suite

## What's included

- `GET /health` — liveness check (the app is up; does not touch the database).
- `GET /health/ready` — readiness check (verifies DB connectivity with `SELECT 1`;
  returns 503 if the database is unreachable).
- A single **base Alembic migration** that enables the `pgvector` extension
  (`CREATE EXTENSION IF NOT EXISTS vector;`). It creates **no tables** — new schema
  migrations chain off this base.
- Reusable infrastructure in `src/` (`database.py`, `deps.py`, `config.py`) for when
  you add models and routers.

## Prerequisites

You only need:

- **Docker** — <https://docs.docker.com/get-docker/>
- **Docker Compose** — bundled with Docker Desktop
- **Git** *(optional)* — only if you clone the repository

You do **not** need Python or PostgreSQL installed on your machine. Everything runs
inside Docker.

## Environment setup

The project is configured through a `.env` file. Copy the provided template:

```bash
# (optional) clone the repository
git clone <your-repo-url>
cd <your-repo>

# create your local environment file
cp .env.example .env
```

The defaults work out of the box. Before using this anywhere real, change
`POSTGRES_PASSWORD` (and the matching password inside `SQLALCHEMY_DATABASE_URL`).

> `.env` is gitignored and must never be committed.

## Running the project

Build the images and start everything:

```bash
docker compose up --build
```

To run it in the background (detached), add `-d`:

```bash
docker compose up -d --build
```

On startup the API container automatically waits for PostgreSQL, applies all Alembic
migrations (which enables `pgvector`), and then starts the server — so the database is
always ready before the API accepts requests.

## Fresh start (reset the database from scratch)

To wipe the database volume and rebuild from an empty database:

```bash
docker compose down -v          # stop the stack AND delete the postgres_data volume
docker compose up -d --build    # entrypoint runs `alembic upgrade head` on boot
docker compose logs -f api      # (optional) watch the migration apply
```

After this the database contains only the `pgvector` extension and Alembic's
`alembic_version` bookkeeping table — **no application tables**.

## Accessing the app

Once the stack is running:

| What | URL |
| --- | --- |
| API root | <http://localhost:8000> |
| Interactive API docs (Swagger) | <http://localhost:8000/docs> |
| Liveness check | <http://localhost:8000/health> |
| Readiness check | <http://localhost:8000/health/ready> |
| Database UI (Adminer) | <http://localhost:8080> |

The host ports are configurable via `API_PORT` and `ADMINER_PORT` in `.env`.

## Database UI

- Start services:

  ```bash
  docker compose up -d
  ```

- Open Adminer:

  <http://localhost:8080>

- In Adminer, use:

  | Setting | Value |
  | --- | --- |
  | System | PostgreSQL |
  | Server | `db` |
  | Username | value of `POSTGRES_USER` (default `postgres`) |
  | Password | value of `POSTGRES_PASSWORD` |
  | Database | value of `POSTGRES_DB` (default `fastapi`) |

- **Important:** inside Adminer the **Server** must be `db`, not `localhost`.
  Adminer runs in its own container, so "localhost" there means the Adminer
  container itself — not your machine and not the database. Because Adminer and
  PostgreSQL share the same Docker Compose network, the database is reached by its
  Compose service name, `db`, on its internal port `5432`.

## Database migrations

Migrations are managed with **Alembic** and run **automatically** every time the API
container starts (see [`entrypoint.sh`](entrypoint.sh)), so you normally don't need to
do anything.

To apply migrations manually:

```bash
docker compose run --rm api alembic upgrade head
```

To create a new migration after adding models:

```bash
docker compose run --rm api alembic revision --autogenerate -m "describe change"
```

## Running tests

The test suite runs inside the API container:

```bash
docker compose run --rm api pytest
```

The tests use an in-memory SQLite database, so they never touch your PostgreSQL data.
The current suite covers `/health` and `/health/ready`.

## Useful Docker commands

```bash
# Build and start in the background
docker compose up -d --build

# Follow logs for a service
docker compose logs -f api
docker compose logs -f db

# Stop the stack
docker compose down

# Stop the stack AND delete the database volume (wipes all data)
docker compose down -v
```

> `docker compose down -v` permanently deletes the PostgreSQL volume and everything
> stored in it.

## Project structure

```text
.
├── src/                  # Application code
│   ├── main.py           # FastAPI app; includes the health router
│   ├── routers/
│   │   ├── __init__.py
│   │   └── health.py     # GET /health and GET /health/ready
│   ├── models.py         # SQLAlchemy Base (no application tables yet)
│   ├── schemas.py        # Pydantic schemas (empty)
│   ├── database.py       # engine / SessionLocal / get_db
│   ├── deps.py           # shared FastAPI dependencies
│   └── config.py         # settings (pydantic-settings)
├── alembic/              # Database migrations (base migration enables pgvector)
├── tests/                # Pytest suite (health checks)
├── docker-compose.yml    # Defines the api, db, and adminer services
├── Dockerfile            # API image
├── entrypoint.sh         # Waits for the DB, migrates, then starts the API
└── .env.example          # Template for your .env
```

## Development notes

- This project is intended to be run through **Docker Compose** — that is the source
  of truth for building and running the backend.
- Host-based setups (virtualenvs, local `pip install`, running `uvicorn` directly) are
  intentionally **not** the documented path. Use Docker.
- Everything you need — running the app, applying migrations, and running tests — is
  available through `docker compose`.
- To build a real feature: add ORM models to `src/models.py`, schemas to
  `src/schemas.py`, a router under `src/routers/` (include it in `src/main.py`), then
  autogenerate a migration that chains off the pgvector base.
