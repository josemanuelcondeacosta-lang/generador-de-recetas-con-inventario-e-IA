import os
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


def make_engine(url: str):
    database = make_url(url)
    if database.drivername in {"postgres", "postgresql"}:
        database = database.set(drivername="postgresql+psycopg")
    if database.get_backend_name() == "sqlite":
        return create_engine(database, connect_args={"check_same_thread": False})
    if os.getenv("DATABASE_TRANSACTION_POOLER") == "1":
        return create_engine(
            database, pool_pre_ping=True, pool_size=1, max_overflow=0,
            connect_args={"prepare_threshold": None, "sslmode": "require"},
        )
    return create_engine(database, pool_pre_ping=True)


def get_db(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session


DB = Annotated[Session, Depends(get_db)]
