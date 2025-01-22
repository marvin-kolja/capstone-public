from unittest.mock import patch, MagicMock

import pytest
from sqlmodel import Session


@pytest.fixture
def mock_db_session():
    db_session_mock = MagicMock(spec=Session)
    with patch.object(Session, "__enter__", return_value=db_session_mock):
        yield db_session_mock
