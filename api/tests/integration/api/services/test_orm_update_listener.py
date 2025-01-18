import asyncio

import pytest

from api.models import Build
from api.services.orm_update_listener import ModelUpdateListener


@pytest.mark.asyncio
async def test_orm_update_listener_updates(db, new_db_fake_build):
    """
    GIVEN: An instance of ModelUpdateListener
    AND: A sql model instance

    WHEN: The listen method is called
    AND: The model instance is updated

    THEN: The listener is registered and updated model instances are streamed
    AND: The listener stops after calling the stop method
    AND: The correct number of updates are received
    """
    listener = ModelUpdateListener(db_instance=new_db_fake_build, model_class=Build)

    async def update_task():
        """Simulate updates"""
        new_db_fake_build.scheme = "Debug"
        db.add(new_db_fake_build)
        db.commit()

        await asyncio.sleep(0.1)

        new_db_fake_build.status = "failure"
        db.add(new_db_fake_build)
        db.commit()

    task = asyncio.create_task(update_task())

    update_count = 0

    async for update in listener.listen():
        if update is not None:
            update_count += 1
            if update_count == 1:
                assert update == new_db_fake_build  # Initial state
            elif update_count == 2:
                assert update.scheme == "Debug"
            elif update_count == 3:
                assert update.status == "failure"
                listener.stop()

    await task
    assert update_count == 3  # Initial state + 2 updates
