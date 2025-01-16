import logging

from sqlmodel import SQLModel

logger = logging.getLogger(__name__)


def update_db_model(
    *, db_model: SQLModel, new_data_model: SQLModel, exclude_unset: bool = True
):
    """
    Update a SQLModel instance with data from another SQLModel instance.

    If `new_data_model` includes keys that do not exist in `db_model`, they will be ignored.

    :param db_model: The instance to update.
    :param new_data_model: The instance containing the new data.

    :param exclude_unset: Whether to exclude unset values from the new_data_model when dumping it.
    """
    logger.debug(f"Updating {db_model} with {new_data_model}.")
    new_data = new_data_model.model_dump(exclude_unset=exclude_unset)
    for key, value in new_data.items():
        if hasattr(db_model, key):
            setattr(db_model, key, value)
        else:
            logger.warning(
                f"Attempted to set attribute {key} on {db_model}, but it does not exist."
            )
    return db_model
