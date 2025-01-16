import pathlib

from sqlalchemy import TypeDecorator, String


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
