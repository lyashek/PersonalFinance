"""Слой доступа к данным: подключение к БД и управление сессиями."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Требуется для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Предоставляет сессию БД для использования в зависимостях FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
