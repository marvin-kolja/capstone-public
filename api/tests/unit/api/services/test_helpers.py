import pytest
from sqlmodel import SQLModel

from api.services.helpers import update_db_model


@pytest.mark.parametrize(
    "new_data",
    [
        {"name": "new name", "age": 20},
        {"name": "new name"},
        {"age": 20},
        {"non_existent_key": "value"},
    ],
)
@pytest.mark.asyncio
async def test_update_db_model(new_data):
    """
    GIVEN: A db_model and a new_data_model

    WHEN: The update_db_model function is called

    THEN: The db_model should be updated with the new_data_model values
    AND: Keys that do not exist in the db_model should be ignored
    """

    class DBModel(SQLModel):
        id: int
        name: str
        age: int

    class NewDataModel(SQLModel):
        name: str | None = None
        age: int | None = None

    db_model = DBModel(id=1, name="name", age=10)
    new_data_model = NewDataModel.model_validate(new_data)

    updated_db_model = update_db_model(db_model=db_model, new_data_model=new_data_model)

    assert updated_db_model.id == 1
    assert updated_db_model.name == new_data.get("name", "name")
    assert updated_db_model.age == new_data.get("age", 10)
    assert hasattr(updated_db_model, "non_existent_key") is False
