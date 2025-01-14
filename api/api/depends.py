from typing import Generator, Annotated

from fastapi import Depends
from sqlmodel import Session

from api.db import engine


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
