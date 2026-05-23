from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from material_ingestion.db.config import load_postgres_settings


def create_db_engine() -> Engine:
    settings = load_postgres_settings()
    return create_engine(settings.sqlalchemy_url, future=True)


def create_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=create_db_engine(), autoflush=False, autocommit=False, expire_on_commit=False)
