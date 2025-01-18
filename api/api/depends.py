from typing import Generator, Annotated

from core.device.i_device_manager import IDeviceManager
from fastapi import Depends
from sqlalchemy import text
from sqlmodel import Session

from api.async_jobs import AsyncJobRunner
from api.db import engine


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        session.execute(
            text("PRAGMA foreign_keys=ON")
        )  # required for SQLite to enforce foreign keys
        yield session


SessionDep = Annotated[Session, Depends(get_db)]

device_manager = IDeviceManager()


def get_device_manager() -> IDeviceManager:
    return device_manager


DeviceManagerDep = Annotated[IDeviceManager, Depends(get_device_manager)]

async_job_runner = AsyncJobRunner()


def get_job_runner() -> AsyncJobRunner:
    return async_job_runner


AsyncJobRunnerDep = Annotated[AsyncJobRunner, Depends(get_job_runner)]
