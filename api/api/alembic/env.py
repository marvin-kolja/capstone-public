import contextlib
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from api.models import SQLModel  # noqa
from api.config import settings  # noqa

target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.SQLALCHEMY_DATABASE_URI_SYNC
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # The following options are required for SQLite to produce correct migrations
        #
        # see: https://alembic.sqlalchemy.org/en/latest/batch.html#batch-migrations
        # and: https://github.com/PrefectHQ/prefect/pull/9169
        transaction_per_migration=True,
        render_as_batch=True,
        template_args={"dialect": "sqlite"},  # used in `script.py.mako`
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.SQLALCHEMY_DATABASE_URI_SYNC
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # The following options are required for SQLite to produce correct migrations
            #
            # see: https://alembic.sqlalchemy.org/en/latest/batch.html#batch-migrations
            # and: https://github.com/PrefectHQ/prefect/pull/9169
            render_as_batch=True,
            transaction_per_migration=True,
        )

        with disable_sqlite_foreign_keys(context):
            with context.begin_transaction():
                context.run_migrations()


@contextlib.contextmanager
def disable_sqlite_foreign_keys(context):
    """
    Disable foreign key constraints on sqlite.
    """
    context.execute("PRAGMA foreign_keys=OFF")

    yield

    context.execute("PRAGMA foreign_keys=ON")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
