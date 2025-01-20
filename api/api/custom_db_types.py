import pathlib

from sqlalchemy import TypeDecorator, String, func, text
from sqlmodel import Field as SQLField


class PathType(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if isinstance(value, pathlib.Path):
            return value.resolve().as_posix()
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return pathlib.Path(value)
        return value


# noinspection PyPep8Naming
def CreatedAtField(
    **kwargs,
) -> SQLField:
    return SQLField(
        sa_column_kwargs={"server_default": func.now()},
        **kwargs,
    )


# noinspection PyPep8Naming
def UpdatedAtField(
    **kwargs,
) -> SQLField:
    return SQLField(
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
        },
        **kwargs,
    )
