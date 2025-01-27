from unittest.mock import patch, MagicMock

import pytest
from sqlmodel import Session

from api.depends import get_db
from api.main import app


@pytest.fixture
def mock_db_session():
    db_session_mock = MagicMock(spec=Session)
    with patch.object(Session, "__enter__", return_value=db_session_mock):
        yield db_session_mock


@pytest.fixture
def mock_db_session_dependencies():
    mock_db_session = MagicMock(spec=Session)

    async def override_db_session():
        return mock_db_session

    app.dependency_overrides[get_db] = override_db_session

    yield mock_db_session

    app.dependency_overrides = {}
