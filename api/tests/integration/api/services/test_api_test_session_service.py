import asyncio
import pathlib
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from core.test_session.session_state import ExecutionStepStateSnapshot
from core.xc.xcresult.models.test_results.summary import TestResult
from fastapi import Request

from api.models import (
    SessionTestPlanPublic,
    BuildPublic,
    DeviceWithStatus,
    TestSession,
    ExecutionStep,
    XcTestResult,
    ExecutionStepPublic,
)

# noinspection PyProtectedMember
from api.services.api_test_session_service import (
    create_test_session,
    _handle_execution_state_snapshot,
    listen_to_execution_step_updates,
)


def test_create_test_session(
    db, new_db_project, new_db_fake_build, new_db_fake_device, new_test_plan
):
    """
    GIVEN: a database session, a project, a build, a device, and a test plan

    WHEN: a test session db entry is created

    THEN: the returned object is a TestSession instance
    AND: the TestSession instance has the correct attributes
    AND: the TestSession instance is the same as the one in the database
    """
    public_plan = SessionTestPlanPublic.model_validate(new_test_plan)
    public_build = BuildPublic.model_validate(new_db_fake_build)
    public_device = DeviceWithStatus.model_validate(new_db_fake_device)

    session = create_test_session(
        session=db,
        public_plan=public_plan,
        public_build=public_build,
        public_device=public_device,
        xc_test_configuration_name="fake_test_config",
        execution_steps=[],
        session_id=None,
    )

    assert session.plan_id == public_plan.id
    assert session.build_id == public_build.id
    assert session.device_id == public_device.id
    assert session.xc_test_configuration_name == "fake_test_config"
    assert session.execution_steps == []
    assert session.id is not None
    assert session.created_at is not None
    assert session.updated_at is not None
    assert SessionTestPlanPublic.model_validate(session.plan_snapshot) == public_plan
    assert BuildPublic.model_validate(session.build_snapshot) == public_build
    assert DeviceWithStatus.model_validate(session.device_snapshot) == public_device

    assert db.get(TestSession, session.id) == session


@pytest.mark.parametrize(
    "status",
    [
        "completed",
        "failed",
        "in_progress",
        "pending",
    ],
)
@pytest.mark.parametrize(
    "trace_path, xcresult_path",
    [
        (None, None),
        (pathlib.Path("/test/trace.trace"), None),
        (None, pathlib.Path("/test/xcresult.xcresult")),
        (pathlib.Path("/test/trace.trace"), pathlib.Path("/test/xcresult.xcresult")),
    ],
)
@pytest.mark.asyncio
async def test_handle_execution_state_updates_task(
    db,
    new_db_fake_test_session,
    new_db_fake_execution_step,
    status,
    trace_path,
    xcresult_path,
    test_summary,
):
    """
    GIVEN: A test session and an execution step in the database
    AND: A new execution state snapshot

    WHEN: The handle_execution_state_updates_task is called

    THEN: The execution step is updated correctly
    """
    db_execution_step = new_db_fake_execution_step
    db_test_session = new_db_fake_test_session

    snapshot_mock = MagicMock(spec=ExecutionStepStateSnapshot)
    snapshot_mock.status = status
    snapshot_mock.trace_path = trace_path
    snapshot_mock.xcresult_path = xcresult_path

    execution_step_mock = MagicMock()
    execution_step_mock.plan_step_order = db_execution_step.plan_step_order
    execution_step_mock.step_repetition = db_execution_step.step_repetition
    execution_step_mock.plan_repetition = db_execution_step.plan_repetition

    snapshot_mock.execution_step = execution_step_mock

    with patch(
        "api.services.api_test_session_service._parse_xcresult_to_xc_test_result_model"
    ) as mock_parse:
        mock_parse.return_value = None

        await _handle_execution_state_snapshot(
            session=db,
            test_session_id=db_test_session.id,
            snapshot=snapshot_mock,
        )

        db_entry = db.get(ExecutionStep, db_execution_step.id)
        assert db_entry.status == status
        assert db_entry.trace_path == trace_path
        assert db_entry.xcresult_path == xcresult_path

        if xcresult_path:
            mock_parse.assert_called_once_with(
                execution_step_id=db_execution_step.id,
                xcresult_path=xcresult_path,
            )


@pytest.mark.asyncio
async def test_listen_to_execution_step_updates(
    db, new_db_fake_execution_step, new_db_fake_test_session
):
    """
    GIVEN: A test session and an execution step in the database
    AND: Simulated updates to the execution step

    WHEN: Listening to execution step updates

    THEN: Only the updates of the execution step should be listened to that are in the test session
    AND: The listener should stop when the test session is completed/failed/cancelled
    """
    request_mock = AsyncMock(spec=Request)
    request_mock.is_disconnected.return_value = False

    new_db_fake_test_session.status = "in_progress"
    db.add(new_db_fake_test_session)
    db.commit()

    async def simulate_updates():
        new_db_fake_execution_step.status = "completed"
        db.add(new_db_fake_execution_step)
        db.commit()

        await asyncio.sleep(0.1)

        new_db_fake_execution_step.xcresult_path = pathlib.Path(
            "/test/xcresult.xcresult"
        )
        db.add(new_db_fake_execution_step)
        db.commit()

        await asyncio.sleep(0.1)

        new_db_fake_execution_step.xc_test_result = XcTestResult(
            skipped_tests=0,
            execution_step_id=new_db_fake_execution_step.id,
            expected_failures=0,
            start_time=0,
            end_time=1,
            failed_tests=0,
            passed_tests=1,
            total_test_count=0,
            test_failures=[],
            result=TestResult.passed,
        )
        db.add(new_db_fake_execution_step)
        db.commit()

        await asyncio.sleep(0.1)

        new_db_fake_test_session.status = "completed"
        db.add(new_db_fake_test_session)
        db.commit()

    task = asyncio.create_task(simulate_updates())

    update_count = 0

    async for event in listen_to_execution_step_updates(
        test_session_id=new_db_fake_test_session.id, request=request_mock
    ):
        update_count += 1

        # event is a json string and ends with two newlines
        assert event.endswith("\n\n")
        json_string = event[:-2]
        assert (
            ExecutionStepPublic.model_validate_json(json_string).id
            == new_db_fake_execution_step.id
        )

    await task

    assert update_count == 3
    request_mock.is_disconnected.assert_called()


@pytest.mark.asyncio
async def test_listen_to_execution_step_updates_disconnect(
    db, new_db_fake_test_session
):
    """
    GIVEN: A test session in the database

    WHEN: Listening to execution step updates

    THEN: The listener should stop when the request is disconnected
    """
    request_mock = AsyncMock(spec=Request)
    request_mock.is_disconnected.side_effect = AsyncMock(return_value=True)

    async for event in listen_to_execution_step_updates(
        test_session_id=new_db_fake_test_session.id, request=request_mock
    ):
        continue

    request_mock.is_disconnected.assert_called()
