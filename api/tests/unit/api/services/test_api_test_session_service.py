import asyncio
import pathlib
import uuid
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock, call

import pytest
from core.test_session import execution_plan
from core.test_session.metrics import Metric

from api.models import SessionTestPlanPublic, SessionTestPlanStepPublic

# noinspection PyProtectedMember
from api.services.api_test_session_service import (
    _parse_api_test_plan_to_core_test_plan,
    plan_execution,
    construct_db_execution_step_model,
    construct_db_execution_step_models,
    get_test_session_dir_path,
    start_test_session,
    _start_test_session_job,
    _parse_xcresult_to_xc_test_result_model,
    _async_execution_state_updates_generator,
)


@pytest.fixture
def fake_public_test_plan_step():
    return SessionTestPlanStepPublic(
        id=uuid.uuid4(),
        name="TestStep1",
        order=0,
        recording_start_strategy="launch",
        reinstall_app=False,
        metrics=[Metric.cpu],
        repetitions=1,
        test_cases=["test/case/1", "test/case/2"],
    )


@pytest.fixture
def fake_public_test_plan(fake_public_test_plan_step):

    return SessionTestPlanPublic(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        name="SampleTestPlan",
        recording_start_strategy="launch",
        reinstall_app=False,
        end_on_failure=True,
        repetitions=2,
        repetition_strategy="entire_suite",
        metrics=[Metric.cpu, Metric.memory],
        steps=[fake_public_test_plan_step],
        xc_test_plan_name="SampleTestPlan",
        recording_strategy="per_step",
    )


def test_plan_execution(fake_public_test_plan):
    """
    GIVEN: A fake public test plan step

    WHEN: The test plan step is parsed to a core execution plan

    THEN: The execution plan should be called with the correct values
    AND: It should be planned
    AND: And the execution plan instance should be returned
    """
    xctetrun_path_mock = MagicMock(spec=pathlib.Path)
    xc_test_configuration_name = "Test Configuration"

    with patch(
        "api.services.api_test_session_service._parse_api_test_plan_to_core_test_plan"
    ) as mock_parse, patch(
        "api.services.api_test_session_service.execution_plan.ExecutionPlan"
    ) as mock_execution_plan:
        mock_parse.return_value = MagicMock()
        mock_execution_plan_instance = MagicMock()
        mock_execution_plan.return_value = mock_execution_plan_instance

        result = plan_execution(
            public_plan=fake_public_test_plan,
            xctestrun_path=xctetrun_path_mock,
            xc_test_configuration_name=xc_test_configuration_name,
        )

        mock_execution_plan.assert_called_once_with(
            test_plan=mock_parse.return_value,
        )
        mock_execution_plan_instance.plan.assert_called_once()
        assert result == mock_execution_plan_instance


def test_construct_db_execution_step_model():
    """
    GIVEN: a fake core execution step

    WHEN: the core execution step is parsed to a database model

    THEN: the database model should be constructed with the correct attributes
    """
    test_session_id = uuid.uuid4()

    expected = {
        "recording_start_strategy": "launch",
        "step_repetition": 1,
        "plan_step_order": 0,
        "metrics": [Metric.cpu],
        "session_id": test_session_id,
        "test_cases": ["test/case/1", "test/case/2"],
        "end_on_failure": True,
        "test_target_name": "TestTarget",
        "plan_repetition": 2,
        "reinstall_app": False,
        "status": "not_started",
    }

    core_execution_step = MagicMock(spec=execution_plan.ExecutionStep)
    core_execution_step.recording_start_strategy = "launch"
    core_execution_step.step_repetition = 1
    core_execution_step.plan_step_order = 0
    core_execution_step.metrics = [Metric.cpu]
    core_execution_step.test_cases = [
        MagicMock(spec=execution_plan.StepTestCase, xctest_id="test/case/1"),
        MagicMock(spec=execution_plan.StepTestCase, xctest_id="test/case/2"),
    ]
    core_execution_step.end_on_failure = True

    test_target_mock = MagicMock(spec=execution_plan.XcTestTarget)
    test_target_mock.BlueprintName = "TestTarget"
    core_execution_step.test_target = test_target_mock

    core_execution_step.plan_repetition = 2
    core_execution_step.reinstall_app = False

    db_execution_step = construct_db_execution_step_model(
        test_session_id=test_session_id,
        core_execution_step=core_execution_step,
    )

    assert (
        db_execution_step.model_dump(exclude={"id", "created_at", "updated_at"})
        == expected
    )


def test_construct_db_execution_step_models():
    """
    GIVEN: a mocked core execution plan

    WHEN: constructing database models for the execution steps

    THEN: the `construct_db_execution_step_model` should be called for each step.
    """
    with patch(
        "api.services.api_test_session_service.construct_db_execution_step_model"
    ) as mock_construct:
        test_session_id = uuid.uuid4()
        core_execution_plan = MagicMock(spec=execution_plan.ExecutionPlan)
        core_execution_plan.execution_steps = [
            MagicMock(spec=execution_plan.ExecutionStep),
            MagicMock(spec=execution_plan.ExecutionStep),
        ]

        construct_db_execution_step_models(
            test_session_id=test_session_id,
            core_execution_plan=core_execution_plan,
        )

        assert mock_construct.call_count == 2


def test_get_test_session_dir_path():
    """
    GIVEN: a test session ID

    WHEN: getting the test session directory path

    THEN: the directory path should be returned
    """
    test_session_id = uuid.UUID("f1b9b1b4-0b3b-4b3b-8b3b-0b3b3b3b3b3b")
    expected = pathlib.Path("/tmp/f1b9b1b40b3b4b3b8b3b0b3b3b3b3b3b")

    with patch("api.services.api_test_session_service.settings") as mock_settings:
        mock_settings.TEST_SESSIONS_DIR_PATH = pathlib.Path("/tmp")

        result = get_test_session_dir_path(test_session_id=test_session_id)

        assert result == expected


def test_start_test_session():
    """
    GIVEN: a test session, a device, a test session ID, and a core execution plan

    WHEN: starting the test session

    THEN: the job runner should add the job to start the test session
    """
    with patch(
        "api.services.api_test_session_service._start_test_session_job"
    ) as mock_start_test_session_job, patch(
        "api.services.api_test_session_service.AsyncJobRunner"
    ) as mock_job_runner:
        session = MagicMock()
        i_device = MagicMock()
        db_test_session = MagicMock()
        core_execution_plan = MagicMock()

        start_test_session(
            session=session,
            i_device=i_device,
            db_test_session=db_test_session,
            job_runner=mock_job_runner,
            core_execution_plan=core_execution_plan,
        )

        mock_job_runner.add_job.assert_called_once_with(
            func=mock_start_test_session_job,
            kwargs={
                "session": session,
                "db_test_session": db_test_session,
                "device": i_device,
                "core_execution_plan": core_execution_plan,
            },
            job_id=db_test_session.id.hex,
        )


@pytest.mark.parametrize(
    "exception, expected_status",
    [
        (None, "completed"),
        (Exception, "failed"),
    ],
)
@pytest.mark.asyncio
async def test_start_test_session_job(exception, expected_status):
    """
    GIVEN: a session, a test session, a device, and a core execution plan

    WHEN: running the test session job

    THEN: the status of the test session should be set to running
    AND: the path to the test session directory should be created
    AND: the test session should be run
    AND: the status of the test session should be set to completed or failed based on any exceptions
    """
    with patch(
        "api.services.api_test_session_service.core_test_session.Session"
    ) as mock_session, patch(
        "api.services.api_test_session_service.get_test_session_dir_path"
    ) as mock_get_test_session_dir_path, patch(
        "api.services.api_test_session_service._handle_execution_state_updates_task"
    ) as mock_handle_execution_state_updates_task:
        db_session = MagicMock()
        db_test_session = MagicMock()
        status_value_mock = PropertyMock()
        type(db_test_session).status = status_value_mock

        device = MagicMock()
        core_execution_plan = MagicMock()

        mock_get_test_session_dir_path.return_value = MagicMock()

        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        if exception:
            mock_session_instance.run = AsyncMock(side_effect=exception)
        else:
            mock_session_instance.run = AsyncMock()

        await _start_test_session_job(
            session=db_session,
            db_test_session=db_test_session,
            device=device,
            core_execution_plan=core_execution_plan,
        )

        mock_get_test_session_dir_path.return_value.mkdir.assert_called_once_with(
            exist_ok=True
        )
        mock_session_instance.run.assert_awaited_once()

        status_value_mock.assert_has_calls(
            [
                call("running"),
                call(expected_status),
            ]
        )

        assert db_session.commit.call_count == 2
        assert db_session.add.call_count == 2

        mock_handle_execution_state_updates_task.assert_called_once()


@pytest.mark.asyncio
async def test_async_execution_state_updates_generator():
    """
    GIVEN: a queue with items
    AND: a stop event

    WHEN: the stop event is set
    AND: the async execution state updates generator is called

    THEN: the queue should be listened to
    AND: the generator should yield all items in the queue
    AND: the generator should stop afterward as the stop event is set
    """
    queue = asyncio.Queue()
    stop_event = asyncio.Event()

    # Fake queue items
    for i in range(3):
        queue.put_nowait(i)
    stop_event.set()  # Tell the generator to stop after the queue is empty

    current_item = 0

    async for item in _async_execution_state_updates_generator(
        queue=queue, stop_event=stop_event
    ):
        assert item == current_item
        current_item += 1

    assert current_item == 3


@pytest.mark.asyncio
async def test_async_execution_state_updates_generator_queue_shutdown():
    """
    GIVEN: a queue that is shut down

    WHEN: the async execution state updates generator is called

    THEN: the generator should stop immediately
    """
    queue = asyncio.Queue()
    queue.shutdown(immediate=True)

    stop_event = asyncio.Event()

    async for item in _async_execution_state_updates_generator(
        queue=queue, stop_event=stop_event
    ):
        assert False, "Should not reach here"

    assert True


@pytest.mark.asyncio
async def test_async_execution_state_updates_generator_empty_queue():
    """
    GIVEN: an empty queue

    WHEN: the async execution state updates generator is called

    THEN: the generator should try to get an item from the queue until the stop event is set
    """
    queue = asyncio.Queue()
    stop_event = asyncio.Event()

    async def delayed_set_stop_event():
        await asyncio.sleep(0.2)
        stop_event.set()

    delay_set_stop_event_task = asyncio.create_task(delayed_set_stop_event())

    with patch.object(queue, "get_nowait") as mock_get:
        mock_get.side_effect = asyncio.QueueEmpty

        async for item in _async_execution_state_updates_generator(
            queue=queue, stop_event=stop_event
        ):
            assert False, "Should not reach here"

        assert mock_get.call_count > 0

    await delay_set_stop_event_task


@pytest.mark.asyncio
async def test_parse_xcresult_to_xc_test_result_model(test_summary):
    """
    GIVEN: a test summary
    AND: an execution step ID
    AND: a path to a xcresult file

    WHEN: parsing the xcresult to a XcTestResult db model

    THEN: the xcresult tool should be called with the correct path
    AND: the db model should be returned with the correct attributes
    """
    execution_step_id = MagicMock(spec=uuid.UUID)
    xcresult_path = pathlib.Path("/path/to/xcresult")

    with patch(
        "api.services.api_test_session_service.XcresultTool"
    ) as mock_xcresult_tool:
        mock_xcresult_tool_instance = AsyncMock()
        mock_xcresult_tool.return_value = mock_xcresult_tool_instance
        mock_xcresult_tool_instance.get_test_summary.return_value = test_summary

        result = await _parse_xcresult_to_xc_test_result_model(
            execution_step_id=execution_step_id,
            xcresult_path=xcresult_path,
        )

        mock_xcresult_tool.assert_called_once_with("/path/to/xcresult")
        assert result.execution_step_id == execution_step_id
        assert result.skipped_tests == test_summary.skipped_tests
        assert result.failed_tests == test_summary.failed_tests
        assert result.passed_tests == test_summary.passed_tests
        assert result.test_failures == test_summary.test_failures
        assert result.total_test_count == test_summary.total_test_count
        assert result.start_time == test_summary.start_time
        assert result.end_time == test_summary.finish_time
        assert result.expected_failures == test_summary.expected_failures


def test_parse_api_test_plan_to_core_test_plan(
    fake_public_test_plan, fake_public_test_plan_step
):
    """
    GIVEN: A fake public test plan

    WHEN: The public test plan is parsed to a core test plan

    THEN: The core test plan should be created with the correct attributes
    """
    xctestrun_path = "/path/to/xctestrun"
    test_configuration = "Debug"

    core_test_plan = _parse_api_test_plan_to_core_test_plan(
        public_plan=fake_public_test_plan,
        xctestrun_path=xctestrun_path,
        test_configuration=test_configuration,
    )

    # Verify core test plan
    assert core_test_plan.name == fake_public_test_plan.name
    assert (
        core_test_plan.recording_start_strategy
        == fake_public_test_plan.recording_start_strategy
    )
    assert core_test_plan.reinstall_app == fake_public_test_plan.reinstall_app
    assert core_test_plan.end_on_failure == fake_public_test_plan.end_on_failure
    assert core_test_plan.repetitions == fake_public_test_plan.repetitions
    assert (
        core_test_plan.repetition_strategy == fake_public_test_plan.repetition_strategy
    )
    assert core_test_plan.metrics == fake_public_test_plan.metrics

    # Verify xctestrun config
    assert core_test_plan.xctestrun_config.path == xctestrun_path
    assert core_test_plan.xctestrun_config.test_configuration == test_configuration

    # Verify steps
    assert len(core_test_plan.steps) == 1
    step = core_test_plan.steps[0]
    assert step.name == fake_public_test_plan_step.name
    assert step.order == fake_public_test_plan_step.order
    assert (
        step.recording_start_strategy
        == fake_public_test_plan_step.recording_start_strategy
    )
    assert step.reinstall_app == fake_public_test_plan_step.reinstall_app
    assert step.metrics == fake_public_test_plan_step.metrics
    assert step.repetitions == fake_public_test_plan_step.repetitions
    assert len(step.test_cases) == len(fake_public_test_plan_step.test_cases)

    # Verify test cases in steps
    expected_test_cases = [tc for tc in fake_public_test_plan_step.test_cases]
    actual_test_cases = [tc.xctest_id for tc in step.test_cases]
    assert actual_test_cases == expected_test_cases
