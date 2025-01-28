import pathlib

import pytest
from core.test_session.metrics import Metric

from api.models import (
    SessionTestPlanStep,
    SessionTestPlan,
    Device,
    XcProject,
    XcProjectScheme,
    XcProjectTarget,
    XcProjectConfiguration,
    XcProjectTestPlan,
    Build,
    Xctestrun,
    TestSession,
    BuildPublic,
    ExecutionStep,
    SessionTestPlanPublic,
    DeviceWithStatus,
    RepetitionStrategy,
)


@pytest.fixture(scope="function")
async def new_test_plan(db, new_db_project, new_db_fake_build) -> SessionTestPlan:
    test_plan = SessionTestPlan(
        name="test plan",
        build_id=new_db_fake_build.id,
        repetitions=1,
        repetition_strategy=RepetitionStrategy.entire_suite,
        metrics=[Metric.cpu],
        project_id=new_db_project.id,
    )
    db.add(test_plan)
    await db.commit()
    await db.refresh(test_plan)

    yield test_plan

    # We specifically do not delete the test plan here, as we want to test that the database can handle multiple test
    # plans existing at the same time.


@pytest.fixture(scope="function")
async def new_test_plan_step(db, new_test_plan) -> SessionTestPlanStep:
    test_plan_step = SessionTestPlanStep(
        name="test step",
        test_plan_id=new_test_plan.id,
        order=0,
        test_cases=["test/case/path"],
    )
    db.add(test_plan_step)
    await db.commit()
    await db.refresh(test_plan_step)
    await db.refresh(new_test_plan)

    yield test_plan_step

    # We specifically do not delete the step here, as we want to test that the database can handle multiple test
    # steps existing at the same time.


@pytest.fixture(scope="function")
async def new_db_fake_device(db, random_device_id) -> Device:
    device = Device(
        id=random_device_id,
        udid=random_device_id,
        device_name="Fake Device",
        device_class="Fake",
        product_version="Fake",
        build_version="Fake",
        product_type="Fake",
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    yield device

    await db.delete(device)
    await db.commit()


@pytest.fixture
async def new_db_project(db, path_to_example_project) -> XcProject:
    project = XcProject(name="project_1", path=path_to_example_project)
    db.add(project)
    await db.commit()

    scheme = XcProjectScheme(name="scheme_1", project_id=project.id)
    target = XcProjectTarget(name="target_1", project_id=project.id)
    configuration = XcProjectConfiguration(
        name="configuration_1", project_id=project.id
    )
    db.add(scheme)
    db.add(target)
    db.add(configuration)
    await db.commit()

    xc_test_plan = XcProjectTestPlan(
        name="xc_test_plan_1", scheme_id=scheme.id, project_id=project.id
    )
    db.add(xc_test_plan)
    await db.commit()

    await db.refresh(scheme)  # Refresh all data attached to the scheme
    await db.refresh(project)  # Refresh all data attached to the project

    return project


@pytest.fixture
async def new_db_fake_build(db, new_db_project, new_db_fake_device) -> Build:
    """
    Add a new build to the database.
    """
    db_build = Build(
        scheme="Release",
        configuration="Release",
        test_plan="RP Swift",
        project_id=new_db_project.id,
        device_id=new_db_fake_device.id,
    )
    db.add(db_build)
    await db.commit()
    await db.refresh(db_build)

    return db_build


@pytest.fixture
async def new_db_fake_xctestrun(db, new_db_fake_build) -> Xctestrun:
    """
    Add a new xctestrun to the database.
    """
    xctestrun = Xctestrun(
        path=pathlib.Path("xctestrun_path"),
        test_configurations=["test_config"],
        build_id=new_db_fake_build.id,
    )
    db.add(xctestrun)
    await db.commit()
    await db.refresh(xctestrun)  # Refresh all data attached

    return xctestrun


@pytest.fixture
async def new_db_fake_test_session(
    db, new_db_fake_build, new_db_fake_device, new_test_plan, new_test_plan_step
) -> TestSession:
    """
    Add a new test session to the database.
    """
    public_build = BuildPublic.model_validate(new_db_fake_build)
    public_device = DeviceWithStatus.model_validate(new_db_fake_device)
    public_plan = SessionTestPlanPublic.model_validate(new_test_plan)

    test_session = TestSession(
        xc_test_configuration_name="test_config",
        plan_id=new_test_plan.id,
        build_id=new_db_fake_build.id,
        device_id=new_db_fake_device.id,
        plan_snapshot=public_plan.model_dump(mode="json"),
        build_snapshot=public_build.model_dump(mode="json"),
        device_snapshot=public_device.model_dump(mode="json"),
    )
    db.add(test_session)
    await db.commit()
    await db.refresh(test_session)  # Refresh all data attached

    return test_session


@pytest.fixture
async def new_db_fake_execution_step(
    db, new_db_fake_test_session, new_test_plan_step, new_test_plan
) -> ExecutionStep:
    """
    Add a new execution step to the database.
    """
    execution_step = ExecutionStep(
        step_repetition=1,
        plan_step_order=0,
        plan_repetition=1,
        session_id=new_db_fake_test_session.id,
        recording_start_strategy=new_test_plan_step.recording_start_strategy
        or new_test_plan.recording_start_strategy,
        test_cases=new_test_plan_step.test_cases,
        metrics=new_test_plan_step.metrics or new_test_plan.metrics,
        reinstall_app=new_test_plan_step.reinstall_app or new_test_plan.reinstall_app,
        end_on_failure=new_test_plan.end_on_failure,
        test_target_name="fake target name",  # TODO: replace with an actual value when needed
    )
    db.add(execution_step)
    await db.commit()
    await db.refresh(execution_step)  # Refresh all data attached

    return execution_step
