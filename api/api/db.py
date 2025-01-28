import logging

from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from api.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI, echo=settings.ENVIRONMENT == "local"
)


def set_sqlite_pragma(dbapi_connection, connection_record):
    logger.critical("Setting PRAGMA foreign_keys=ON for SQLite connection")
    # Required for SQLite to enforce foreign keys
    dbapi_connection.execute("PRAGMA foreign_keys = ON;")


# Set the SQLite PRAGMA foreign_keys=ON for every new connection
listen(engine.sync_engine, "connect", set_sqlite_pragma)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
)
