"""Dependencies para FastAPI - sessão e repositório"""
from pathlib import Path
from apps.backend.src.infrastructure.database.setup import SessionLocal, init_db
from apps.backend.src.infrastructure.repositories_db import SqlAlchemyRepository


def get_repo():
    """Yield repository instance. init_db on first use."""
    init_db()
    session = SessionLocal()
    try:
        yield SqlAlchemyRepository(session)
    finally:
        session.close()
