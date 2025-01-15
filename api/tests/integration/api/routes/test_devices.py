import pytest
from fastapi.testclient import TestClient


def test_list_devices(
    client: TestClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the list_devices endpoint is called

    THEN: The response should be a list of devices
    AND: The list should contain the real device
    """
    if real_device is None:
        pytest.skip("Not implemented yet")

    r = client.get("/devices/")
    assert r.status_code == 200

    data = r.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    matching_devices = [device for device in data if device["id"] == real_device.udid]
    assert len(matching_devices) == 1


def test_read_device(
    client: TestClient,
    real_device,
):
    """
    GIVEN: a real device

    WHEN: the read_device endpoint is called

    THEN: The response should be the real device
    """
    if real_device is None:
        pytest.skip("Not implemented yet")

    r = client.get(f"/devices/{real_device.udid}")
    assert r.status_code == 200

    data = r.json()

    assert isinstance(data, dict)
    assert data["id"] == real_device.udid


def test_read_device_not_found(client: TestClient, random_device_id):
    """
    GIVEN: a device id that does not exist

    WHEN: the read_device endpoint is called

    THEN: The response should be a 404
    """
    r = client.get(f"/devices/{random_device_id}")
    assert r.status_code == 404
