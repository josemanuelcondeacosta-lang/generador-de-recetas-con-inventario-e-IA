import os
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def make_engine(url: str):
    options = {"check_same_thread": False} if url.startswith("sqlite:") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=options)


def get_db() -> Iterator[Session]:
    from app.main import engine

    with Session(engine) as session:
        yield session


DB = Annotated[Session, Depends(get_db)]
