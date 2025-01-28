import pytest
from sqlmodel import SQLModel

from api.models import Build
from api.services.orm_update_listener import ModelUpdateListener


@pytest.mark.asyncio
async def test_orm_update_listener_invalid_instance():
    """
    GIVEN: An instance of ModelUpdateListener
    AND: A sql model instance

    WHEN: The db_instance is not an instance of the model_class

    THEN: A ValueError is raised
    """
    with pytest.raises(ValueError):
        ModelUpdateListener(db_instance=SQLModel(), model_class=Build)


@pytest.mark.asyncio
async def test_orm_update_listener_no_instance():
    """
    GIVEN: An instance of ModelUpdateListener
    AND: A sql model instance

    WHEN: The db_instance is None

    THEN: The listener is created without an initial state
    """
    listener = ModelUpdateListener(model_class=Build)
    assert listener._queue.empty()
