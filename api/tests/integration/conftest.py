import pathlib
from typing import Generator, AsyncGenerator

import pytest
from core.device.i_device import IDevice
from core.device.i_device_manager import IDeviceManager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import async_session_maker


@pytest.fixture
async def db() -> AsyncSession:
    async with async_session_maker() as session:
        await session.execute(
            text("PRAGMA foreign_keys=ON")
        )  # required for SQLite to enforce foreign keys
        yield session


@pytest.fixture(scope="session")
def real_device() -> IDevice:
    device_manager = IDeviceManager()
    devices = device_manager.list_devices()
    if devices:
        return devices[0]


@pytest.fixture(scope="session")
def path_to_example_project() -> pathlib.Path:
    return (
        pathlib.Path(__file__).parent.parent.parent.parent
        / "misc"
        / "example_apps"
        / "RP Swift"
        / "RP Swift.xcodeproj"
    )
