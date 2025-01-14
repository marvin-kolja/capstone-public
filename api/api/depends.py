from typing import Generator, Annotated

from core.device.i_device_manager import IDeviceManager
from fastapi import Depends
from sqlmodel import Session

from api.db import engine


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]

device_manager = IDeviceManager()


def get_device_manager() -> IDeviceManager:
    return device_manager


DeviceManagerDep = Annotated[IDeviceManager, Depends(get_device_manager)]
