import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_devices(
    async_client: AsyncClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the list_devices endpoint is called

    THEN: The response should be a list of devices
    AND: The list should contain the real device
    """
    if real_device is None:
        pytest.skip("Requires a real device to be connected")

    r = await async_client.get("/devices/")
    assert r.status_code == 200

    data = r.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    matching_devices = [device for device in data if device["id"] == real_device.udid]
    assert len(matching_devices) == 1


@pytest.mark.asyncio
async def test_read_device(
    async_client: AsyncClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the read_device endpoint is called

    THEN: The response should be the real device
    """
    if real_device is None:
        pytest.skip("Requires a real device to be connected")

    r = await async_client.get(f"/devices/{real_device.udid}")
    assert r.status_code == 200

    data = r.json()

    assert isinstance(data, dict)
    assert data["id"] == real_device.udid


@pytest.mark.asyncio
async def test_read_device_not_found(async_client: AsyncClient, random_device_id):
    """
    GIVEN: a device id that does not exist

    WHEN: the read_device endpoint is called

    THEN: The response should be a 404
    """
    r = await async_client.get(f"/devices/{random_device_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_pair_device(
    async_client: AsyncClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the pair_device endpoint is called

    THEN: The response should be a 200
    """
    if real_device is None:
        pytest.skip("Requires a real device to be connected")

    if real_device.paired:
        real_device.unpair()

    r = await async_client.post(f"/devices/{real_device.udid}/pair")

    assert r.status_code == 200

    r_2 = await async_client.post(
        f"/devices/{real_device.udid}/pair"
    )  # Pairing the same device twice should not fail.

    assert r_2.status_code == 200


@pytest.mark.asyncio
async def test_unpair_device(
    async_client: AsyncClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the unpair_device endpoint is called

    THEN: The response should be a 200
    AND: The response should be a 400 when called twice
    """
    if real_device is None:
        pytest.skip("Requires a real device to be connected")

    await async_client.post(
        f"/devices/{real_device.udid}/pair"
    )  # Make sure the device is paired first.

    r = await async_client.post(f"/devices/{real_device.udid}/unpair")

    assert r.status_code == 200

    r_2 = await async_client.post(
        f"/devices/{real_device.udid}/unpair"
    )  # Unpairing the same device twice should fail.

    assert r_2.status_code == 500


@pytest.mark.asyncio
async def test_enable_developer_mode(
    async_client: AsyncClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the enable_developer_mode endpoint is called

    THEN: The response should be a 200
    """
    # NOTE: This is a little hard to test as disabling developer mode would require manual doing so on the device.

    if real_device is None:
        pytest.skip("Requires a real device to be connected")

    await async_client.post(
        f"/devices/{real_device.udid}/pair"
    )  # Make sure the device is paired first.

    r = await async_client.post(f"/devices/{real_device.udid}/developer-mode/enable")

    if not real_device.requires_developer_mode:
        assert r.status_code == 400
    elif real_device.developer_mode_enabled:
        assert r.status_code == 400
    else:
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_mount_ddi(
    async_client: AsyncClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the mount_ddi endpoint is called

    THEN: The response should be a 200
    AND: The response should be a 400 when called twice
    """
    if real_device is None:
        pytest.skip("Requires a real device to be connected")

    await async_client.post(
        f"/devices/{real_device.udid}/pair"
    )  # Make sure the device is paired first.
    await async_client.post(
        f"/devices/{real_device.udid}/ddi/unmount"
    )  # Unmount the DDI first

    r = await async_client.post(f"/devices/{real_device.udid}/ddi/mount")

    assert r.status_code == 200

    r_2 = await async_client.post(
        f"/devices/{real_device.udid}/ddi/mount"
    )  # Mounting the same device twice should fail.

    assert r_2.status_code == 400


@pytest.mark.asyncio
async def test_unmount_ddi(
    async_client: AsyncClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the unmount_ddi endpoint is called

    THEN: The response should be a 200
    AND: The response should be a 400 when called twice
    """
    if real_device is None:
        pytest.skip("Requires a real device to be connected")

    await async_client.post(
        f"/devices/{real_device.udid}/pair"
    )  # Make sure the device is paired first.
    await async_client.post(
        f"/devices/{real_device.udid}/ddi/mount"
    )  # Mount the DDI first

    r = await async_client.post(f"/devices/{real_device.udid}/ddi/unmount")

    assert r.status_code == 200

    r_2 = await async_client.post(
        f"/devices/{real_device.udid}/ddi/unmount"
    )  # Unmounting the same device twice should fail.

    assert r_2.status_code == 400
