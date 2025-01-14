from sqlmodel import SQLModel, Field as SQLField


class DeviceBase(SQLModel):
    device_class: str
    device_name: str
    build_version: str
    product_version: str
    product_type: str


class Device(DeviceBase, table=True):
    __tablename__ = "device"

    id: str = SQLField(primary_key=True)
    udid: str = SQLField(
        unique=True
    )  # For now, it is the same as id, but we may want to change the primary key to something else
