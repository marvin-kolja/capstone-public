import asyncio
import logging
import pathlib
import uuid
from contextlib import suppress
from typing import Optional, AsyncGenerator

from core.device.i_device import IDevice
from core.test_session.session_state import ExecutionStepStateSnapshot
from core.xc.xcresult.xcresulttool import XcresultTool
from core.xc.xctrace.xctrace_interface import Xctrace
from core.xc.xctrace.xml_parser import Schema, Sysmon, ProcessStdoutErr, CoreAnimation
from fastapi import Request
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from core.test_session import (
    plan as core_plan,
    execution_plan,
    session as core_test_session,
)

from api.async_jobs import AsyncJobRunner
from api.config import settings
from api.db import engine
from api.models import (
    TestSession,
    ExecutionStep,
    SessionTestPlanPublic,
    BuildPublic,
    DeviceWithStatus,
    XcTestResult,
    ExecutionStepPublic,
    SysmonDB,
    ProcessStdoutErrDB,
    CoreAnimationDB,
    TraceResultDataBase,
    TraceResult,
    RecordingStartStrategy,
)
from api.services.orm_update_listener import ModelUpdateListener

logger = logging.getLogger(__name__)


def list_test_sessions(*, session: Session) -> list[TestSession]:
    """
    List all test sessions in the database.
    """
    return list(
        session.exec(
            select(TestSession).options(selectinload(TestSession.execution_steps))
        ).all()
    )


def read_test_session(
    *, session: Session, test_session_id: uuid.UUID
) -> Optional[TestSession]:
    """
    Read a test session from the database by its ID.
    """
    return session.get(TestSession, test_session_id)


def plan_execution(
    *,
    public_plan: SessionTestPlanPublic,
    xctestrun_path: pathlib.Path,
    xc_test_configuration_name: str,
) -> execution_plan.ExecutionPlan:
    """
    Plan the test session execution based on the public test plan, xctestrun path and test configuration.

    :param public_plan: The public test plan model
    :param xctestrun_path: The path to the xctestrun file
    :param xc_test_configuration_name: The test configuration to be used

    :return: The core execution plan model
    """
    core_session_test_plan = _parse_api_test_plan_to_core_test_plan(
        public_plan=public_plan,
        xctestrun_path=xctestrun_path.resolve().as_posix(),
        test_configuration=xc_test_configuration_name,
    )
    core_execution_plan = execution_plan.ExecutionPlan(test_plan=core_session_test_plan)
    core_execution_plan.plan()
    return core_execution_plan


def create_test_session(
    *,
    session: Session,
    public_plan: SessionTestPlanPublic,
    public_build: BuildPublic,
    public_device: DeviceWithStatus,
    xc_test_configuration_name: str,
    execution_steps: list[ExecutionStep] = None,
    session_id: Optional[uuid.UUID] = None,
) -> TestSession:
    """
    Create a new test session in the database.

    :param session: The database session
    :param public_plan: The public test plan model to create a snapshot of
    :param public_build: The public build model to create a snapshot of
    :param public_device: The public device model to create a snapshot of
    :param xc_test_configuration_name: The test configuration name to be used for execution
    :param execution_steps: The execution steps to be used for the test session
    :param session_id: The UUID of the test session
    :return: The database test session model
    """
    db_test_session = TestSession(
        id=session_id,
        plan_id=public_plan.id,
        plan_snapshot=public_plan.model_dump(mode="json"),
        build_id=public_build.id,
        build_snapshot=public_build.model_dump(mode="json"),
        device_id=public_device.id,
        device_snapshot=public_device.model_dump(mode="json"),
        execution_steps=execution_steps,
        xc_test_configuration_name=xc_test_configuration_name,
    )
    session.add(db_test_session)
    session.commit()
    session.refresh(db_test_session)
    return db_test_session


def construct_db_execution_step_models(
    *,
    test_session_id: uuid.UUID,
    core_execution_plan: execution_plan.ExecutionPlan,
) -> list[ExecutionStep]:
    """
    Constructs a list of database models for the execution steps using the test session ID and the core execution plan.
    """
    return [
        construct_db_execution_step_model(
            test_session_id=test_session_id,
            core_execution_step=core_execution_step,
        )
        for core_execution_step in core_execution_plan.execution_steps
    ]


def construct_db_execution_step_model(
    *,
    test_session_id: uuid.UUID,
    core_execution_step: execution_plan.ExecutionStep,
) -> ExecutionStep:
    """
    Constructs a database model for the execution step using the test session ID and the core execution step.
    """

    return ExecutionStep(
        recording_start_strategy=RecordingStartStrategy.from_string(
            core_execution_step.recording_start_strategy
        ),
        step_repetition=core_execution_step.step_repetition,
        plan_step_order=core_execution_step.plan_step_order,
        metrics=core_execution_step.metrics,
        session_id=test_session_id,
        test_cases=[
            test_case.xctest_id for test_case in core_execution_step.test_cases
        ],
        end_on_failure=core_execution_step.end_on_failure,
        test_target_name=core_execution_step.test_target.BlueprintName,
        plan_repetition=core_execution_step.plan_repetition,
        reinstall_app=core_execution_step.reinstall_app,
    )


def start_test_session(
    *,
    i_device: IDevice,
    test_session_id: uuid.UUID,
    job_runner: AsyncJobRunner,
    core_execution_plan: execution_plan.ExecutionPlan,
):
    """
    Start the test session in the background by adding the job to the job runner.
    """
    job_runner.add_job(
        func=_start_test_session_job,
        kwargs={
            "test_session_id": test_session_id,
            "device": i_device,
            "core_execution_plan": core_execution_plan,
        },
        job_id=test_session_id.hex,
    )


def get_test_session_dir_path(*, test_session_id: uuid.UUID) -> pathlib.Path:
    """
    Return the path to the directory where the test session data is stored.
    """
    return settings.TEST_SESSIONS_DIR_PATH / test_session_id.hex


async def _start_test_session_job(
    *,
    test_session_id: uuid.UUID,
    device: IDevice,
    core_execution_plan: execution_plan.ExecutionPlan,
):
    """
    Execute the test session and update the status of the test session in the database based on the result.
    """
    with Session(engine) as session:
        db_test_session = read_test_session(
            session=session, test_session_id=test_session_id
        )
        db_test_session.status = "running"
        session.add(db_test_session)
        session.commit()

        stop_event = asyncio.Event()
        update_handler_task: Optional[asyncio.Task] = None

        try:
            output_dir = get_test_session_dir_path(test_session_id=db_test_session.id)
            output_dir.mkdir(exist_ok=True)

            queue: asyncio.Queue[ExecutionStepStateSnapshot] = asyncio.Queue()

            test_session = core_test_session.Session(
                session_id=db_test_session.id,
                device=device,
                execution_plan=core_execution_plan,
                output_dir=output_dir,
                queue=queue,
            )

            update_handler_task = asyncio.create_task(
                _handle_execution_state_updates_task(
                    session=session,
                    test_session_id=db_test_session.id,
                    stop_event=stop_event,
                    queue=queue,
                )
            )
            await test_session.run()

            db_test_session.status = "completed"
            session.add(db_test_session)
            session.commit()
        except asyncio.CancelledError:
            logger.info(f"Test session '{db_test_session.id}' was cancelled")
            db_test_session.status = "cancelled"
            session.add(db_test_session)
            session.commit()
        except Exception as e:
            logger.error(
                f"Error running test session '{db_test_session.id}'", exc_info=e
            )
            db_test_session.status = "failed"
            session.add(db_test_session)
            session.commit()
        finally:
            stop_event.set()
            with suppress(asyncio.CancelledError):
                if update_handler_task:
                    await update_handler_task


async def _handle_execution_state_updates_task(
    *,
    session: Session,
    test_session_id: uuid.UUID,
    stop_event: asyncio.Event,
    queue: asyncio.Queue[ExecutionStepStateSnapshot],
) -> None:
    async for snapshot in _async_execution_state_updates_generator(
        stop_event=stop_event, queue=queue
    ):
        await _handle_execution_state_snapshot(
            session=session, test_session_id=test_session_id, snapshot=snapshot
        )


async def _async_execution_state_updates_generator(
    *,
    stop_event: asyncio.Event,
    queue: asyncio.Queue[ExecutionStepStateSnapshot],
) -> AsyncGenerator[ExecutionStepStateSnapshot, None]:
    """
    Generate the execution state updates from the queue until the stop event is set.

    :param stop_event: The event to stop the generator. When set, the generator will stop generating updates after the
    queue is empty.
    :param queue: The queue to get the execution state updates from
    """
    while True:
        try:
            if stop_event.is_set() and queue.empty():
                break

            snapshot = queue.get_nowait()
            yield snapshot
        except asyncio.QueueEmpty:
            await asyncio.sleep(0.1)
        except asyncio.QueueShutDown:
            logger.critical(
                f"Queue to get session state updates was shutdown unexpectedly"
            )
            break


async def _handle_execution_state_snapshot(
    *,
    session: Session,
    test_session_id: uuid.UUID,
    snapshot: ExecutionStepStateSnapshot,
):
    """
    Handle the execution state snapshot by updating the database execution step model with the snapshot data.

    If the snapshot has a xcresult path, this will be parsed and saved to the database as well.

    :param session: Session to use for database operations
    :param test_session_id: The ID of the test session
    :param snapshot: The snapshot of the execution step state
    """
    db_execution_step = session.exec(
        select(ExecutionStep).where(
            ExecutionStep.session_id == test_session_id,
            ExecutionStep.plan_step_order == snapshot.execution_step.plan_step_order,
            ExecutionStep.step_repetition == snapshot.execution_step.step_repetition,
            ExecutionStep.plan_repetition == snapshot.execution_step.plan_repetition,
        )
    ).one()

    db_execution_step.status = snapshot.status
    db_execution_step.trace_path = snapshot.trace_path
    db_execution_step.xcresult_path = snapshot.xcresult_path

    if snapshot.xcresult_path:
        xc_test_result = await _parse_xcresult_to_xc_test_result_model(
            execution_step_id=db_execution_step.id,
            xcresult_path=snapshot.xcresult_path,
        )
        db_execution_step.xc_test_result = xc_test_result

    session.add(db_execution_step)
    session.commit()


async def _parse_xcresult_to_xc_test_result_model(
    *,
    execution_step_id: uuid.UUID,
    xcresult_path: pathlib.Path,
) -> Optional[XcTestResult]:
    """
    Parse the xcresult file to a database test result model.

    :param execution_step_id: The ID of the execution step in the database
    :param xcresult_path: The path to the xcresult file

    :return: The database test result model
    """
    xcresult_tool = XcresultTool(xcresult_path.resolve().as_posix())
    try:
        summary = await xcresult_tool.get_test_summary()
    except Exception as e:
        logger.warning("Failed to parse xcresult summary", exc_info=e)
        return None

    db_xc_test_result = XcTestResult(
        execution_step_id=execution_step_id,
        result=summary.result,
        skipped_tests=summary.skipped_tests,
        failed_tests=summary.failed_tests,
        passed_tests=summary.passed_tests,
        test_failures=summary.test_failures,
        total_test_count=summary.total_test_count,
        start_time=summary.start_time,
        end_time=summary.finish_time,
        expected_failures=summary.expected_failures,
    )
    return db_xc_test_result


def _parse_api_test_plan_to_core_test_plan(
    *,
    public_plan: SessionTestPlanPublic,
    xctestrun_path: str,
    test_configuration: str,
) -> core_plan.SessionTestPlan:
    """
    Parse the public test plan model to the core test plan model.

    This can be used to validate the test plan against the requirements of the core test plan model.

    :param public_plan: The public test plan model
    :param xctestrun_path: The path to the xctestrun file. Not required if just validating the test plan
    :param test_configuration: The test configuration to be used. Not required if just validating the test plan

    :raises ValidationError:

    :return: The core test plan model
    """
    return core_plan.SessionTestPlan(
        name=public_plan.name,
        recording_start_strategy=public_plan.recording_start_strategy.to_literal(),
        reinstall_app=public_plan.reinstall_app,
        end_on_failure=public_plan.end_on_failure,
        repetitions=public_plan.repetitions,
        repetition_strategy=public_plan.repetition_strategy.to_literal(),
        metrics=public_plan.metrics,
        xctestrun_config=core_plan.XctestrunConfig(
            path=xctestrun_path,
            test_configuration=test_configuration,
        ),
        steps=[
            core_plan.PlanStep(
                name=step.name,
                order=step.order,
                recording_start_strategy=step.recording_start_strategy.to_literal(),
                reinstall_app=step.reinstall_app,
                metrics=step.metrics,
                repetitions=step.repetitions,
                test_cases=[
                    core_plan.StepTestCase(
                        xctest_id=case,
                    )
                    for case in step.test_cases
                ],
            )
            for step in public_plan.steps
        ],
    )


def generate_session_id() -> uuid.UUID:
    """
    Generate a new UUID for a test session.
    """
    return uuid.uuid4()


def session_is_done(*, session: Session, test_session_id: uuid.UUID) -> bool:
    """
    Check if the test session is done (completed, failed or cancelled).

    :param session: The database session to use
    :param test_session_id: The ID of the test session
    :return:
    """
    db_test_session = read_test_session(
        session=session, test_session_id=test_session_id
    )
    return db_test_session.status in {"completed", "failed", "cancelled"}


async def listen_to_execution_step_updates(
    *, test_session_id: uuid.UUID, request: Request
) -> AsyncGenerator[str, None]:
    """
    An async generator that listens to updates of a build and yields the updated build.

    This is done until the build status is set to 'success' or 'failure', or the request is disconnected.
    """

    listener: ModelUpdateListener[ExecutionStep] = ModelUpdateListener(
        db_instance=None,
        model_class=ExecutionStep,
    )

    async for update in listener.listen():
        with Session(engine) as session:
            is_done = session_is_done(session=session, test_session_id=test_session_id)

            if update is None:
                if await request.is_disconnected():
                    logger.debug(f"Request disconnected, stopping listener")
                    listener.stop()
                if is_done:
                    logger.debug(
                        f"Test session '{test_session_id}' status is done, stopping listener"
                    )
                    listener.stop()
                continue

            if update.session_id != test_session_id:
                continue  # Skip updates for other test sessions

            yield "data: " + ExecutionStepPublic.model_validate(
                update
            ).model_dump_json() + "\n\n"


def process_trace_results_job_id(*, test_session_id: uuid.UUID) -> str:
    """
    Return the job ID for processing the trace results of a test session.
    """
    return "process_trace_results-" + test_session_id.hex


def process_trace_results(*, test_session_id: uuid.UUID, job_runner: AsyncJobRunner):
    """
    Start processing the trace results of a test session in the background
    """
    job_runner.add_job(
        func=_process_trace_results_job,
        kwargs={"test_session_id": test_session_id},
        job_id=process_trace_results_job_id(test_session_id=test_session_id),
    )


async def _process_trace_results_job(*, test_session_id: uuid.UUID):
    """
    Process the trace results of each execution step of a test session.

    :param test_session_id: The ID of the test session
    """
    with Session(engine) as session:
        db_test_session = read_test_session(
            session=session, test_session_id=test_session_id
        )

        for db_execution_step in db_test_session.execution_steps:
            try:
                await process_execution_step_trace_results(
                    session=session, db_execution_step=db_execution_step
                )
            except ValueError:
                logger.debug(
                    f"Skipping processing of trace results for execution step '{db_execution_step.id}'"
                )
                pass


async def process_execution_step_trace_results(
    *, session: Session, db_execution_step: ExecutionStep
):
    """
    Start processing the trace results of a test session.

    - Parses the trace file of the execution step and stores the results in the database.
    - Updates the trace result export status in the database.

    :raises ValueError: If the execution step has no trace path or the trace result export status is 'completed' or
    'running'.
    """
    if not db_execution_step.trace_path:
        logger.warning(f"Execution step '{db_execution_step.id}' has no trace path")
        raise ValueError

    if db_execution_step.trace_result is None:
        db_execution_step.trace_result = TraceResult(
            execution_step_id=db_execution_step.id,
        )

    if db_execution_step.trace_result.export_status == "completed":
        logger.debug(
            f"Execution step '{db_execution_step.id}' trace results already exported"
        )
        raise ValueError
    if db_execution_step.trace_result.export_status == "running":
        logger.warning(
            f"Execution step '{db_execution_step.id}' trace results export already running"
        )
        raise ValueError

    try:
        db_execution_step.trace_result.export_status = "running"

        combined_data = await process_trace_file(
            trace_path=db_execution_step.trace_path
        )
        store_trace_results(
            session=session,
            trace_result_id=db_execution_step.trace_result.id,
            data=combined_data,
        )

        db_execution_step.trace_result.export_status = "completed"
    except asyncio.CancelledError:
        logger.info(
            f"Processing trace file '{db_execution_step.trace_path}' was cancelled"
        )
        db_execution_step.trace_result.export_status = "cancelled"
        raise
    except Exception as e:
        logger.error(
            f"Error processing trace file '{db_execution_step.trace_path}'",
            exc_info=e,
        )
        db_execution_step.trace_result.export_status = "failed"
    finally:
        session.add(db_execution_step)
        session.commit()


async def process_trace_file(
    *, trace_path: pathlib.Path
) -> list[Sysmon | ProcessStdoutErr | CoreAnimation]:
    """
    Export the trace file to a toc and data file, and parse the data file to a dictionary using the toc file.

    :param trace_path: The path to the trace file
    :return: A list of all parsed data from the trace file. The list can contain multiple types of Schema data.
    """
    if not trace_path.exists():
        raise FileNotFoundError(f"Trace file '{trace_path}' does not exist")

    stem = trace_path.stem
    parent = trace_path.parent
    toc_path = parent / (stem + "_toc.xml")
    data_path = parent / (stem + "_data.xml")

    toc_path.unlink(missing_ok=True)
    data_path.unlink(missing_ok=True)

    await Xctrace.export_toc(
        trace_path=trace_path.as_posix(),
        toc_path=toc_path.as_posix(),
    )
    await Xctrace.export_data(
        trace_path=trace_path.as_posix(),
        data_path=data_path.as_posix(),
        schemas=Schema.all(),
        run=1,
    )
    toc = Xctrace.parse_toc_xml(toc_path.as_posix())
    data = Xctrace.parse_data_xml(data_path.as_posix(), toc=toc)

    single_run = data[0]

    sysmon = single_run.get(Schema.SYSMON_PROCESS)
    stdouterr = single_run.get(Schema.STDOUTERR_OUTPUT)
    core_animation = single_run.get(Schema.CORE_ANIMATION_FPS_ESTIMATE)

    merged_data = []

    if sysmon:
        merged_data.extend(sysmon)
    if stdouterr:
        merged_data.extend(stdouterr)
    if core_animation:
        merged_data.extend(core_animation)

    return merged_data


def store_trace_results(
    *,
    session: Session,
    trace_result_id: uuid.UUID,
    data: list[Sysmon | ProcessStdoutErr | CoreAnimation],
):
    """
    Store the parsed trace results of a test session in the database.

    :param session: The database session
    :param trace_result_id: The ID of the trace result in the database
    :param data: The parsed trace results data. List can have multiple types of different schema data. The method will
    store the data based on the schema type.
    """
    logger.debug(f"Storing trace results for trace result ID '{trace_result_id}'")
    if not data:
        return

    for item in data:
        model_class: type[TraceResultDataBase]

        if isinstance(item, Sysmon):
            model_class = SysmonDB
        elif isinstance(item, ProcessStdoutErr):
            model_class = ProcessStdoutErrDB
        elif isinstance(item, CoreAnimation):
            model_class = CoreAnimationDB
        else:
            raise ValueError(f"Unknown data type: {item}")

        db_instance = model_class(
            trace_result_id=trace_result_id,
            **item.model_dump(),
        )

        session.add(db_instance)
    session.commit()
