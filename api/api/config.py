import pathlib
from typing import Literal

from pydantic import (
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=False,
        extra="ignore",
    )
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    PROJECT_NAME: str

    SQLITE_PATH: str

    # noinspection PyPep8Naming
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return "sqlite:///" + self.SQLITE_PATH

    BUILD_DIR: str

    # noinspection PyPep8Naming
    @computed_field
    @property
    def BUILD_DIR_PATH(self) -> pathlib.Path:
        path = pathlib.Path(self.BUILD_DIR)
        if not path.exists():
            raise ValueError(f"BUILD_DIR does not exist: {path}")
        return path

    TEST_SESSIONS_DIR: str

    # noinspection PyPep8Naming
    @computed_field
    @property
    def TEST_SESSIONS_DIR_PATH(self) -> pathlib.Path:
        path = pathlib.Path(self.TEST_SESSIONS_DIR)
        if not path.exists():
            raise ValueError(f"TEST_SESSIONS_DIR does not exist: {path}")
        return path


settings = Settings()  # type: ignore
