import pytest
from sqlmodel import select

from api.models import DeviceWithStatus, Device
from api.services import device_service
from tests.conftest import assert_base_device_equal_to_idevice


@pytest.mark.asyncio
async def test_list_devices_connected(
    db, mock_device_manager, mock_i_device, random_device_id
):
    """
    GIVEN: a new device is discovered

    WHEN: the list_devices service function is called

    THEN: The device should be in the list of devices
    AND: the device should be stored in the database
    """
    mock_i_device.udid = random_device_id
    mock_device_manager.list_devices.return_value = [mock_i_device]

    devices = await device_service.list_devices(
        session=db,
        device_manager=mock_device_manager,
    )

    assert len(devices) >= 1
    matching_devices = [device for device in devices if device.id == random_device_id]
    assert len(matching_devices) == 1
    device = matching_devices[0]

    assert device.udid == random_device_id
    assert_base_device_equal_to_idevice(device, mock_i_device)
    assert device.connected is True
    assert device.status == mock_i_device.status

    statement = select(Device).where(Device.udid == random_device_id)
    db_entry = (await db.execute(statement)).scalars().all()

    assert len(db_entry) == 1
    assert db_entry[0] == Device.model_validate(device)


@pytest.mark.asyncio
async def test_list_devices_not_connected(db, mock_device_manager, random_device_id):
    """
    GIVEN: a device is not connected, but stored in DB

    WHEN: the list_devices service function is called

    THEN: The device should be in the list of devices with connected=False and status=None
    """
    device_to_store = Device(
        id=random_device_id,
        udid=random_device_id,
        device_name="DeviceName",
        device_class="iPhone",
        build_version="22B91",
        product_type="iPhone14,4",
        product_version="18.1.1",
    )
    db.add(device_to_store)
    await db.commit()

    devices = await device_service.list_devices(
        session=db,
        device_manager=mock_device_manager,
    )

    assert len(devices) >= 1

    matching_devices = [device for device in devices if device.id == random_device_id]
    assert len(matching_devices) == 1
    device = matching_devices[0]

    assert device == DeviceWithStatus.model_validate(device_to_store)


@pytest.mark.asyncio
async def test_list_devices_db_update(
    db, mock_device_manager, mock_i_device, random_device_id
):
    """
    GIVEN: a stored device
    AND: a connected device with the same id has different information

    WHEN: the list_devices service function is called

    THEN: The device should be in the list of devices with the new information
    AND: The device in the database should be updated
    """
    device_to_store = Device(
        id=random_device_id,
        udid=random_device_id,
        device_name="OldName",
        device_class="old_class",
        build_version="old_version",
        product_type="old_type",
        product_version="old_version",
    )
    db.add(device_to_store)
    await db.commit()

    mock_device_manager.list_devices.return_value = [mock_i_device]

    devices = await device_service.list_devices(
        session=db,
        device_manager=mock_device_manager,
    )

    assert len(devices) >= 1

    matching_devices = [device for device in devices if device.id == random_device_id]
    assert len(matching_devices) == 1
    device = matching_devices[0]

    assert device.udid == mock_i_device.udid
    assert_base_device_equal_to_idevice(device, mock_i_device)
    assert device.connected is True
    assert device.status == mock_i_device.status

    statement = select(Device).where(Device.udid == random_device_id)
    db_entry = (await db.execute(statement)).scalar_one()

    assert db_entry == Device.model_validate(device)


@pytest.mark.asyncio
async def test_get_device_by_id_db(db, mock_device_manager, random_device_id):
    """
    GIVEN: a device is stored in the database

    WHEN: the read_device service function is called

    THEN: The device should be returned
    """
    mock_device_manager.get_device.return_value = None

    device_added_to_db = Device(
        id=random_device_id,
        udid=random_device_id,
        device_name="DeviceName",
        device_class="iPhone",
        build_version="22B91",
        product_type="iPhone14,4",
        product_version="18.1.1",
    )

    db.add(device_added_to_db)
    await db.commit()

    device = await device_service.get_device_by_id(
        device_id=random_device_id, session=db, device_manager=mock_device_manager
    )

    assert device == DeviceWithStatus.model_validate(device_added_to_db)


@pytest.mark.asyncio
async def test_get_device_by_id_connected(
    db, mock_device_manager, mock_i_device, random_device_id
):
    """
    GIVEN: a device is connected

    WHEN: the read_device service function is called

    THEN: The device should be returned
    """
    mock_i_device.udid = random_device_id
    mock_device_manager.get_device.return_value = mock_i_device

    device = await device_service.get_device_by_id(
        device_id=random_device_id, session=db, device_manager=mock_device_manager
    )

    assert device.id == random_device_id
    assert device.udid == random_device_id
    assert_base_device_equal_to_idevice(device, mock_i_device)
    assert device.connected is True
    assert device.status == mock_i_device.status


@pytest.mark.asyncio
async def test_get_device_by_id_not_found(db, mock_device_manager, random_device_id):
    """
    GIVEN: no device is stored in the database

    WHEN: the read_device service function is called

    THEN: None should be returned
    """
    mock_device_manager.get_device.return_value = None

    device = await device_service.get_device_by_id(
        device_id=random_device_id, session=db, device_manager=mock_device_manager
    )

    assert device is None
