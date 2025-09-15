from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlmodel import create_engine, Session
from app.core.config import get_settings

settings = get_settings()

# For Postgres; tweak pool sizes as needed
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    future=True,
)

def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session

@contextmanager
def session_scope() -> Iterator[Session]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()