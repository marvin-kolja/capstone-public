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
)


@pytest.fixture(scope="function")
def new_test_plan(db, new_db_project):
    test_plan = SessionTestPlan(
        name="test plan",
        xc_test_plan_name=new_db_project.schemes[0].xc_test_plans[0].name,
        repetitions=1,
        repetition_strategy="entire_suite",
        metrics=[Metric.cpu],
        project_id=new_db_project.id,
    )
    db.add(test_plan)
    db.commit()
    db.refresh(test_plan)

    yield test_plan

    # We specifically do not delete the test plan here, as we want to test that the database can handle multiple test
    # plans existing at the same time.


@pytest.fixture(scope="function")
def new_test_plan_step(db, new_test_plan):
    test_plan_step = SessionTestPlanStep(
        name="test step",
        test_plan_id=new_test_plan.id,
        order=0,
        test_cases=["test/case/path"],
    )
    db.add(test_plan_step)
    db.commit()
    db.refresh(test_plan_step)
    db.refresh(new_test_plan)

    yield test_plan_step

    # We specifically do not delete the step here, as we want to test that the database can handle multiple test
    # steps existing at the same time.


@pytest.fixture(scope="function")
def new_db_fake_device(db, random_device_id):
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
    db.commit()
    db.refresh(device)

    yield device

    db.delete(device)
    db.commit()


@pytest.fixture
def new_db_project(db, path_to_example_project):
    project = XcProject(name="project_1", path=path_to_example_project)
    db.add(project)
    db.commit()

    scheme = XcProjectScheme(name="scheme_1", project_id=project.id)
    target = XcProjectTarget(name="target_1", project_id=project.id)
    configuration = XcProjectConfiguration(
        name="configuration_1", project_id=project.id
    )
    db.add(scheme)
    db.add(target)
    db.add(configuration)
    db.commit()

    xc_test_plan = XcProjectTestPlan(
        name="xc_test_plan_1", scheme_id=scheme.id, project_id=project.id
    )
    db.add(xc_test_plan)
    db.commit()

    return project


@pytest.fixture
def new_db_fake_build(db, new_db_project, new_db_fake_device):
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
    db.commit()

    return db_build


@pytest.fixture
def new_db_fake_xctestrun(db, new_db_fake_build):
    """
    Add a new xctestrun to the database.
    """
    xctestrun = Xctestrun(
        path=pathlib.Path("xctestrun_path"),
        test_configurations=["test_config"],
        build_id=new_db_fake_build.id,
    )
    db.add(xctestrun)
    db.commit()

    return xctestrun


@pytest.fixture
def new_db_fake_test_session(
    db, new_db_fake_build, new_db_fake_device, new_test_plan, new_test_plan_step
):
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
    db.commit()

    return test_session


@pytest.fixture
def new_db_fake_execution_step(
    db, new_db_fake_test_session, new_test_plan_step, new_test_plan
):
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
    db.commit()

    return execution_step
