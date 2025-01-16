from typing import Generator

import pytest
from core.device.i_device import IDevice
from core.device.i_device_manager import IDeviceManager
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session, delete

from api.db import engine
from api.models import Device
from api.main import app


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
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
