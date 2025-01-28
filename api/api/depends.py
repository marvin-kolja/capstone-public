import logging
from typing import Generator, Annotated, AsyncGenerator

from core.device.i_device_manager import IDeviceManager
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.async_jobs import AsyncJobRunner
from api.db import async_session_maker

logger = logging.getLogger(__name__)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        logger.debug("Creating database session")
        yield session
        logger.debug("Closing database session")


AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

device_manager = IDeviceManager()


def get_device_manager() -> IDeviceManager:
    return device_manager


DeviceManagerDep = Annotated[IDeviceManager, Depends(get_device_manager)]

async_job_runner = AsyncJobRunner()


def get_job_runner() -> AsyncJobRunner:
    return async_job_runner


AsyncJobRunnerDep = Annotated[AsyncJobRunner, Depends(get_job_runner)]
