from __future__ import annotations

import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from vsuet_accounting.infrastructure.db.init_db import (
    database_is_empty,
    init_db,
    seed_data,
)
from vsuet_accounting.infrastructure.db.session import SessionLocal, get_engine


def wait_for_db(retries: int = 30, delay: float = 1.0) -> None:
    engine = get_engine()
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except SQLAlchemyError:
            time.sleep(delay)

    raise RuntimeError("Database is not ready after waiting.")


def bootstrap() -> None:
    engine = get_engine()
    wait_for_db()
    init_db(engine, seed=False)

    with SessionLocal() as session:
        if database_is_empty(session):
            seed_data(session)


if __name__ == "__main__":
    bootstrap()
