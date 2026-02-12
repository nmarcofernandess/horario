from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from .orm_models import Base
from .extended_orm import ShiftORM, CycleTemplateORM, SundayRotationORM

# DB Path
DB_Path = Path(__file__).resolve().parents[3] / "data" / "compliance_engine.db"
DB_URL = f"sqlite:///{DB_Path}"

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Create tables
    DB_Path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
