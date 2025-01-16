import pathlib
from typing import Generator

import pytest
from core.device.i_device import IDevice
from core.device.i_device_manager import IDeviceManager
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlmodel import Session, delete

from api.db import engine
from api.models import Device
from api.main import app


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        session.execute(
            text("PRAGMA foreign_keys=ON")
        )  # required for SQLite to enforce foreign keys
        yield session
        statement = delete(Device)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
async def async_client() -> Generator[AsyncClient, None, None]:
    async with AsyncClient(
        transport=ASGITransport(
            app=app,
        ),
        base_url="http://test",
    ) as ac:
        yield ac


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
