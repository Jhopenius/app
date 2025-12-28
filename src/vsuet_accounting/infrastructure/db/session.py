from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from vsuet_accounting.config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
