from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.depends import get_async_session
from api.main import app


@pytest.fixture
def mock_db_session():
    db_session_mock = AsyncMock(spec=AsyncSession)

    with patch.object(AsyncSession, "__aenter__", return_value=db_session_mock):
        yield db_session_mock


@pytest.fixture
def mock_db_session_dependencies():
    mock_db_session = AsyncMock(spec=AsyncSession)

    async def override_db_session():
        return mock_db_session

    app.dependency_overrides[get_async_session] = override_db_session

    yield mock_db_session

    app.dependency_overrides = {}
