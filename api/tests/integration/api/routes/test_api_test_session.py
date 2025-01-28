import pytest

from api.models import TestSessionPublic


@pytest.mark.asyncio
async def test_list_test_sessions(
    async_client, new_db_fake_test_session, new_db_fake_execution_step
):
    """
    GIVEN: a test session in the database with an execution step

    WHEN: GETing the `/test-session/` endpoint

    THEN: it should return a list of test sessions
    AND: the list should contain the test session
    """
    r = await async_client.get("/test-sessions/")

    assert r.status_code == 200

    data = r.json()

    assert len(data) >= 1

    found = False
    for test_session in data:
        validated_test_session = TestSessionPublic.model_validate(test_session)

        if validated_test_session.id == new_db_fake_test_session.id:
            assert test_session == validated_test_session.model_dump(mode="json")
            assert len(validated_test_session.execution_steps) == 1
            found = True
            break
    assert found, "Test session not found in the response"


@pytest.mark.asyncio
async def test_list_test_sessions_filter_by_project(
    async_client, new_db_fake_test_session, new_db_fake_execution_step, new_db_project
):
    """
    GIVEN: a test session in the database with an execution step

    WHEN: GETing the `/test-sessions/` endpoint with a project_id query parameter that

    THEN: it should return a list of test sessions related to the project
    """
    r = await async_client.get(f"/test-sessions/?project_id={new_db_project.id}")

    assert r.status_code == 200

    data = r.json()

    assert len(data) == 1

    public_test_session = TestSessionPublic.model_validate(data[0])

    assert public_test_session.build_snapshot.project_id == new_db_project.id


@pytest.mark.asyncio
async def test_list_test_sessions_invalid_query(async_client):
    """
    GIVEN: No test sessions in the database

    WHEN: GETing the `/test-sessions/` endpoint with an invalid project_id query parameter

    THEN: it should return a 422
    """
    r = await async_client.get("/test-sessions/?project_id=1")

    assert r.status_code == 422
    assert r.json()["code"] == 422
    assert r.json()["detail"][0]["loc"] == ["query", "project_id"]


@pytest.mark.asyncio
async def test_read_test_session(
    async_client, new_db_fake_test_session, new_db_fake_execution_step
):
    """
    GIVEN: a test session in the database with an execution step

    WHEN: GETing the `/test-sessions/{test_session_id}` endpoint

    THEN: it should return the test session
    """
    r = await async_client.get(f"/test-sessions/{new_db_fake_test_session.id}")

    assert r.status_code == 200

    data = r.json()

    validated_test_session = TestSessionPublic.model_validate(data)

    assert data == validated_test_session.model_dump(mode="json")
    assert len(validated_test_session.execution_steps) == 1


@pytest.mark.asyncio
async def test_read_test_session_not_found(async_client, new_db_fake_test_session):
    """
    GIVEN: No matching test session in the database

    WHEN: GETing the `/test-sessions/{test_session_id}` endpoint

    THEN: it should return a 404
    """
    r = await async_client.get("/test-sessions/00000000-0000-0000-0000-000000000000")

    assert r.status_code == 404
    assert r.json() == {"code": 404, "detail": "Test session not found"}
