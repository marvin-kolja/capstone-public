import asyncio
import pathlib
import uuid
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock, call

import pytest
from core.test_session import execution_plan
from core.test_session.metrics import Metric
from core.xc.xctrace.xml_parser import Schema, Sysmon, ProcessStdoutErr, CoreAnimation
from sqlmodel import Session

from api.async_jobs import AsyncJobRunner
from api.models import (
    SessionTestPlanPublic,
    SessionTestPlanStepPublic,
    ExecutionStep,
    TraceResult,
    RecordingStartStrategy,
    RepetitionStrategy,
    RecordingStrategy,
)

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
    session_is_done,
    process_trace_file,
    store_trace_results,
    process_execution_step_trace_results,
    _process_trace_results_job,
    process_trace_results,
    process_trace_results_job_id,
)


@pytest.fixture
def fake_public_test_plan_step():
    return SessionTestPlanStepPublic(
        id=uuid.uuid4(),
        name="TestStep1",
        order=0,
        recording_start_strategy=RecordingStartStrategy.launch,
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
        recording_start_strategy=RecordingStartStrategy.launch,
        reinstall_app=False,
        end_on_failure=True,
        repetitions=2,
        repetition_strategy=RepetitionStrategy.entire_suite,
        metrics=[Metric.cpu, Metric.memory],
        steps=[fake_public_test_plan_step],
        build_id=uuid.uuid4(),
        recording_strategy=RecordingStrategy.per_step,
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
        i_device = MagicMock()
        db_test_session = MagicMock()
        core_execution_plan = MagicMock()

        start_test_session(
            i_device=i_device,
            test_session_id=db_test_session.id,
            job_runner=mock_job_runner,
            core_execution_plan=core_execution_plan,
        )

        mock_job_runner.add_job.assert_called_once_with(
            func=mock_start_test_session_job,
            kwargs={
                "test_session_id": db_test_session.id,
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
async def test_start_test_session_job(exception, expected_status, mock_db_session):
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
    ) as mock_handle_execution_state_updates_task, patch(
        "api.services.api_test_session_service.read_test_session"
    ) as mock_read_test_session:
        db_test_session = MagicMock()
        mock_read_test_session.return_value = db_test_session
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
            test_session_id=db_test_session.id,
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

        assert mock_db_session.commit.call_count == 2
        assert mock_db_session.add.call_count == 2

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


@pytest.mark.asyncio
async def test_parse_xcresult_to_xc_test_result_model_exception():
    """
    GIVEN: a path to a xcresult file

    WHEN: parsing the xcresult to a XcTestResult db model
    AND: the `XcresultTool.get_test_summary` raises an exception

    THEN: None should be returned
    """
    with patch(
        "api.services.api_test_session_service.XcresultTool"
    ) as mock_xcresult_tool:
        mock_xcresult_tool_instance = AsyncMock()
        mock_xcresult_tool.return_value = mock_xcresult_tool_instance
        mock_xcresult_tool_instance.get_test_summary.side_effect = Exception

        result = await _parse_xcresult_to_xc_test_result_model(
            execution_step_id=uuid.uuid4(),
            xcresult_path=pathlib.Path("/path/to/xcresult"),
        )

        assert result is None


@pytest.mark.parametrize(
    "repetition_strategy",
    [
        RepetitionStrategy.entire_suite,
        RepetitionStrategy.per_step,
    ],
)
@pytest.mark.parametrize(
    "recording_strategy",
    [
        RecordingStrategy.per_step,
        RecordingStrategy.per_test,
    ],
)
@pytest.mark.parametrize(
    "recording_start_strategy",
    [
        RecordingStartStrategy.launch,
        RecordingStartStrategy.attach,
    ],
)
def test_parse_api_test_plan_to_core_test_plan(
    fake_public_test_plan,
    fake_public_test_plan_step,
    repetition_strategy,
    recording_strategy,
    recording_start_strategy,
):
    """
    GIVEN: A fake public test plan

    WHEN: The public test plan is parsed to a core test plan

    THEN: The core test plan should be created with the correct attributes
    """
    xctestrun_path = "/path/to/xctestrun"
    test_configuration = "Debug"

    fake_public_test_plan.repetition_strategy = repetition_strategy
    fake_public_test_plan.recording_strategy = recording_strategy
    fake_public_test_plan.recording_start_strategy = recording_start_strategy
    fake_public_test_plan_step.recording_start_strategy = recording_start_strategy

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
    assert core_test_plan.recording_strategy == fake_public_test_plan.recording_strategy
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


@pytest.mark.parametrize(
    "status",
    [
        "completed",
        "failed",
        "cancelled",
    ],
)
def test_session_is_done(status):
    """
    GIVEN: A test session

    WHEN: Checking if the test session is done

    THEN: The function should return True if the status is completed, failed, or cancelled
    """
    test_session = MagicMock()
    test_session.status = status

    with patch("api.services.api_test_session_service.read_test_session") as mock_read:
        mock_read.return_value = test_session

        assert session_is_done(
            session=MagicMock(), test_session_id=uuid.uuid4()
        ), f"Session should be done if status is {status}"


@pytest.mark.asyncio
async def test_process_trace_results_schedules_and_runs_job():
    """
    GIVEN: a test session ID

    WHEN: calling `process_trace_results`

    THEN: It should schedule as job
    AND: The `_process_trace_results_job` should be called
    """
    job_runner = AsyncJobRunner()
    job_runner.start_scheduler()
    test_session_id = uuid.uuid4()

    with patch(
        "api.services.api_test_session_service._process_trace_results_job"
    ) as mock_process_trace_results_job:
        mock_process_trace_results_job.side_effect = AsyncMock()

        process_trace_results(test_session_id=test_session_id, job_runner=job_runner)

        assert job_runner.job_exists(
            process_trace_results_job_id(test_session_id=test_session_id)
        ), "The job should be scheduled"

        await asyncio.sleep(0.1)

        mock_process_trace_results_job.assert_called_once_with(
            test_session_id=test_session_id
        )

    job_runner.shutdown_scheduler()


@pytest.fixture
def trace_result_mock():
    trace_result_mock = MagicMock(spec=TraceResult)
    trace_result_mock.export_status = "not_started"

    return trace_result_mock


@pytest.fixture
def execution_step_mock(trace_result_mock):
    execution_step_mock = MagicMock(spec=ExecutionStep)
    execution_step_mock.trace_path = "/path/to/trace"
    execution_step_mock.trace_result = trace_result_mock

    return execution_step_mock


@pytest.mark.asyncio
async def test_process_trace_results_job(execution_step_mock, mock_db_session):
    """
    GIVEN: a test session ID

    WHEN: calling `_process_trace_results_job`

    THEN: It should get the current test session form the DB
    AND: Call the `process_execution_step_trace_results` function for each execution step
    """
    test_session_mock = MagicMock()
    test_session_mock.execution_steps = [
        execution_step_mock,
        execution_step_mock,
        execution_step_mock,
    ]

    with patch(
        "api.services.api_test_session_service.read_test_session",
        return_value=test_session_mock,
    ), patch(
        "api.services.api_test_session_service.process_execution_step_trace_results"
    ) as mock_process_execution_step_trace_results:
        await _process_trace_results_job(
            test_session_id=MagicMock(spec=uuid.UUID),
        )

        mock_process_execution_step_trace_results.assert_has_calls(
            [
                call(session=mock_db_session, db_execution_step=execution_step_mock)
                for _ in range(3)
            ]
        )


@pytest.mark.asyncio
async def test_process_execution_step_trace_results_no_trace_file(execution_step_mock):
    """
    GIVEN: an execution step with no trace file

    WHEN: processing the trace results

    THEN: a ValueError should be raised
    AND: the db sessions add or commit should not be called
    """
    db_session = MagicMock(spec=Session)
    execution_step_mock.trace_path = None

    with pytest.raises(ValueError):
        await process_execution_step_trace_results(
            session=db_session,
            db_execution_step=execution_step_mock,
        )

    assert db_session.add.call_count == 0
    assert db_session.commit.call_count == 0


@pytest.mark.parametrize(
    "export_status",
    [
        "running",
        "completed",
    ],
)
@pytest.mark.asyncio
async def test_process_execution_step_trace_results_already_running_or_complete(
    export_status, execution_step_mock, trace_result_mock
):
    """
    GIVEN: an execution step with a trace file and a status of running or completed

    WHEN: processing the trace results

    THEN: None should be returned
    """
    db_session = MagicMock(spec=Session)

    execution_step_mock.trace_path = "/path/to/trace"
    trace_result_mock.export_status = export_status

    with pytest.raises(ValueError):
        await process_execution_step_trace_results(
            session=db_session,
            db_execution_step=execution_step_mock,
        )

    assert db_session.add.call_count == 0
    assert db_session.commit.call_count == 0


@pytest.mark.asyncio
async def test_process_execution_step_trace_results_cancel(
    execution_step_mock, trace_result_mock
):
    """
    GIVEN: an execution with a trace file

    WHEN: processing the trace results
    AND: cancelling the function

    THEN: The asyncio.CancelledError should be raised
    AND: The export status should be set to cancelled
    """

    async def simulate_work(*args, **kwargs):
        await asyncio.sleep(0.5)

    db_session = MagicMock(spec=Session)
    execution_step_mock.trace_path = "/path/to/trace"
    trace_result_mock.export_status = "not_started"

    with patch(
        "api.services.api_test_session_service.process_trace_file"
    ) as process_trace_file_mock, patch(
        "api.services.api_test_session_service.store_trace_results"
    ):
        process_trace_file_mock.side_effect = simulate_work
        task = asyncio.create_task(
            process_execution_step_trace_results(
                session=db_session,
                db_execution_step=execution_step_mock,
            )
        )
        await asyncio.sleep(0.1)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        assert trace_result_mock.export_status == "cancelled"


@pytest.mark.asyncio
async def test_process_execution_step_trace_results_failure(
    execution_step_mock, trace_result_mock
):
    """
    GIVEN: an execution with a trace file

    WHEN: processing the trace results
    AND: the trace file processing fails

    THEN: The export status should be set to failed
    """

    db_session = MagicMock(spec=Session)
    execution_step_mock.trace_path = "/path/to/trace"
    trace_result_mock.export_status = "not_started"

    with patch(
        "api.services.api_test_session_service.process_trace_file"
    ) as process_trace_file_mock, patch(
        "api.services.api_test_session_service.store_trace_results"
    ):
        process_trace_file_mock.side_effect = Exception

        await process_execution_step_trace_results(
            session=db_session,
            db_execution_step=execution_step_mock,
        )

        assert trace_result_mock.export_status == "failed"


@pytest.mark.asyncio
async def test_process_trace_file_success():
    """
    GIVEN: a trace file

    WHEN: processing the trace file

    THEN: the correct methods should be called
    AND: the correct values should be returned
    """
    fake_trace_path = pathlib.Path("/path/to/some-id.trace")

    sysmon_mock = MagicMock()
    stdouterr_mock = MagicMock()
    core_animation_fps_estimate_mock = MagicMock()

    parse_data_xml_return = [
        {
            Schema.SYSMON_PROCESS: [sysmon_mock],
            Schema.STDOUTERR_OUTPUT: [stdouterr_mock],
            Schema.CORE_ANIMATION_FPS_ESTIMATE: [core_animation_fps_estimate_mock],
        }
    ]

    with patch(
        "api.services.api_test_session_service.Xctrace"
    ) as mock_xctrace, patch.object(pathlib.Path, "exists", return_value=True):
        mock_xctrace.export_toc = AsyncMock()
        mock_xctrace.export_data = AsyncMock()
        mock_xctrace.parse_toc_xml = MagicMock()
        mock_xctrace.parse_data_xml = MagicMock(return_value=parse_data_xml_return)

        result = await process_trace_file(
            trace_path=fake_trace_path,
        )

        mock_xctrace.export_toc.assert_awaited_once_with(
            trace_path="/path/to/some-id.trace",
            toc_path="/path/to/some-id_toc.xml",
        )
        mock_xctrace.export_data.assert_awaited_once_with(
            trace_path="/path/to/some-id.trace",
            data_path="/path/to/some-id_data.xml",
            schemas=Schema.all(),
            run=1,
        )
        mock_xctrace.parse_toc_xml.assert_called_once_with(
            "/path/to/some-id_toc.xml",
        )
        mock_xctrace.parse_data_xml.assert_called_once_with(
            "/path/to/some-id_data.xml",
            toc=mock_xctrace.parse_toc_xml.return_value,
        )

        assert result == [
            sysmon_mock,
            stdouterr_mock,
            core_animation_fps_estimate_mock,
        ], "The result should be the parsed data from the trace file"


@pytest.mark.asyncio
async def test_process_trace_file_trace_does_not_exist():
    """
    GIVEN: a trace file that does not exist

    WHEN: processing the trace file

    THEN: an empty list should be returned
    """
    fake_trace_path = pathlib.Path("/path/to/some-id.trace")

    with patch.object(pathlib.Path, "exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            await process_trace_file(trace_path=fake_trace_path)


def test_store_trace_results_invalid_type():
    """
    GIVEN: list of trace results with invalid type

    WHEN: Trying to store them

    THEN: a ValueError should be raised
    """

    with pytest.raises(ValueError):
        store_trace_results(
            session=MagicMock(),
            trace_result_id=MagicMock(spec=uuid.UUID),
            data=[1, 2, 3],
        )


async def test_store_trace_results_session_add():
    """
    GIVEN: list of trace results

    WHEN: Storing them

    THEN: the session should be called to add all trace results
    AND: the session should commit the changes
    """
    session_mock = MagicMock(spec=Session)

    store_trace_results(
        session=session_mock,
        trace_result_id=uuid.uuid4(),
        data=[
            MagicMock(spec=Sysmon),
            MagicMock(spec=ProcessStdoutErr),
            MagicMock(spec=CoreAnimation),
        ],
    )

    assert session_mock.add.call_count == 3
    assert session_mock.commit.call_count == 1
