from api.models import TestSessionPublic


def test_list_test_sessions(
    client, new_db_fake_test_session, new_db_fake_execution_step
):
    """
    GIVEN: a test session in the database with an execution step

    WHEN: GETing the `/test-session/` endpoint

    THEN: it should return a list of test sessions
    AND: the list should contain the test session
    """
    r = client.get("/test-sessions/")

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


def test_read_test_session(
    client, new_db_fake_test_session, new_db_fake_execution_step
):
    """
    GIVEN: a test session in the database with an execution step

    WHEN: GETing the `/test-sessions/{test_session_id}` endpoint

    THEN: it should return the test session
    """
    r = client.get(f"/test-sessions/{new_db_fake_test_session.id}")

    assert r.status_code == 200

    data = r.json()

    validated_test_session = TestSessionPublic.model_validate(data)

    assert data == validated_test_session.model_dump(mode="json")
    assert len(validated_test_session.execution_steps) == 1


def test_read_test_session_not_found(client, new_db_fake_test_session):
    """
    GIVEN: No matching test session in the database

    WHEN: GETing the `/test-sessions/{test_session_id}` endpoint

    THEN: it should return a 404
    """
    r = client.get("/test-sessions/00000000-0000-0000-0000-000000000000")

    assert r.status_code == 404
    assert r.json() == {"detail": "Test session not found"}
