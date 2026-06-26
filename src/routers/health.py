from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from deps import db_dependency

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Liveness: the process is up and able to serve requests.

    Does not touch the database, so it stays green even with zero application
    tables or while the database is unreachable.
    """
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: db_dependency):
    """Readiness: confirm database connectivity with a trivial ``SELECT 1``.

    Returns 503 if the database can't be reached, so orchestrators can hold
    traffic until the DB is actually available.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - needs a real broken DB
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready"}
