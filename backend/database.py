"""Legacy SQLAlchemy scaffold kept for older experiments.

The live Alias backend uses `db.py` plus sqlite and does not import this
module from `main.py`. Keep this layer fail-closed so an accidental import
does not create a second, silently divergent persistence path.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()

engine = (
    create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
    if DATABASE_URL
    else None
)

SessionLocal = (
    sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    if engine is not None
    else None
)


class Base(DeclarativeBase):
    pass


def get_db():
    if SessionLocal is None:
        raise RuntimeError(
            "Legacy SQLAlchemy layer is not configured. "
            "The live backend uses db.py for runtime persistence."
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
