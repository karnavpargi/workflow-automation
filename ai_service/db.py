"""pgvector / Postgres connection helpers for the AI service.

The ``pgvector_reachable`` check is a fast TCP probe used by
``/readyz``. Full ``PGVector`` store wiring is implemented in Task 5.
"""

from urllib.parse import urlparse

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ai_service.config import settings


def pgvector_reachable() -> bool:
    """Return True if Postgres is reachable and the ``vector`` ext is installed.

    Returns:
        Reachability flag.
    """
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
        return True
    except SQLAlchemyError:
        return False
    except Exception:  # noqa: BLE001
        return False


def vector_store_url() -> str:
    """Return a normalized DSN suitable for ``langchain_postgres.PGVector``.

    ``langchain-postgres`` wants a plain ``postgresql://`` DSN without
    the ``+psycopg`` driver suffix that SQLAlchemy accepts.
    """
    parsed = urlparse(settings.database_url)
    return f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}{parsed.path}"


# Silence unused-import lints while keeping the module self-documenting.
_ = httpx
