from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings


def _create_engine(database_url: str):
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # needed for SQLite
    )


engine = _create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def reconfigure_engine(database_url: str) -> None:
    global engine

    engine.dispose()
    settings.DATABASE_URL = database_url
    engine = _create_engine(database_url)
    SessionLocal.configure(bind=engine)


def dispose_engine() -> None:
    engine.dispose()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
