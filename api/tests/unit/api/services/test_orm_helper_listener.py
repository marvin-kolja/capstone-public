import pytest
from sqlmodel import SQLModel

from api.models import Build
from api.services.orm_update_listener import ModelUpdateListener


def test_orm_update_listener_invalid_instance():
    """
    GIVEN: An instance of ModelUpdateListener
    AND: A sql model instance

    WHEN: The db_instance is not an instance of the model_class

    THEN: A ValueError is raised
    """
    with pytest.raises(ValueError):
        ModelUpdateListener(db_instance=SQLModel(), model_class=Build)
