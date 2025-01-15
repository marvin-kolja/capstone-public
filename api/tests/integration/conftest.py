import random
import string
from typing import Generator
from unittest.mock import patch

import pytest
from core.device.i_device import IDevice
from core.device.i_device_manager import IDeviceManager
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from api.config import settings
from api.db import engine
from api.db_models import Device
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
def real_device() -> IDevice:
    device_manager = IDeviceManager()
    devices = device_manager.list_devices()
    if devices:
        return devices[0]


@pytest.fixture
def random_device_id():
    """
    Generate a random device ID like "00000000-0000000000000000"
    """
    return (
        "".join(random.choices(string.digits, k=8))
        + "-"
        + "".join(random.choices(string.digits + string.ascii_uppercase, k=16))
    )
