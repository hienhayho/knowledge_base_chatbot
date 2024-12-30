from sqlmodel import Session
from fastapi import Depends
from typing import Annotated

from src.database import get_session

SessionDeps = Annotated[Session, Depends(get_session)]


def get_session_deps():
    return SessionDeps
