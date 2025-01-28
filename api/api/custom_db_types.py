import datetime
import pathlib

from core.xc.xcresult.models.test_results import summary as xcresult_test_summary
from sqlalchemy import TypeDecorator, String, func, DateTime, Column, JSON
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


class UTCDateTime(TypeDecorator):
    """
    Custom SQLAlchemy type that ensures datetime values are stored in UTC and formatted correctly when retrieved.
    """

    impl = DateTime

    def process_bind_param(self, value, dialect):
        """
        Converts input datetime to UTC before storing it.
        """
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)

    def process_result_value(self, value, dialect):
        """
        Ensures retrieved datetime includes 'Z' (UTC indicator) instead of '+00:00'.
        """
        if value is None:
            return None
        return (
            value.replace(tzinfo=datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )


# noinspection PyPep8Naming
def CreatedAtField(
    **kwargs,
) -> SQLField:
    return SQLField(
        sa_column=Column(UTCDateTime(), server_default=func.now()),
        **kwargs,
    )


# noinspection PyPep8Naming
def UpdatedAtField(
    **kwargs,
) -> SQLField:
    return SQLField(
        sa_column=Column(UTCDateTime(), server_default=func.now(), onupdate=func.now()),
        **kwargs,
    )
