from api.models import SessionTestPlanPublic, BuildPublic, DeviceWithStatus, TestSession
from api.services.api_test_session_service import create_test_session


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
