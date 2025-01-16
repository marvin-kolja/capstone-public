import uuid

import pytest
from core.test_session.metrics import Metric
from fastapi import HTTPException
from sqlmodel import select

from api.db_models import (
    SessionTestPlanStep,
    SessionTestPlan,
    SessionTestPlanPublic,
    SessionTestPlanStepPublic,
    SessionTestPlanCreate,
    SessionTestPlanUpdate,
    SessionTestPlanStepCreate,
    SessionTestPlanStepUpdate,
)

# noinspection PyProtectedMember
from api.services.api_test_plan_service import (
    list_test_plans,
    read_test_plan,
    create_test_plan,
    update_test_plan,
    delete_test_plan,
    create_test_plan_step,
    update_test_plan_step,
    delete_test_plan_step,
    reorder_test_plan_steps,
    _get_test_plan_or_raise,
    _get_test_plan_step,
    _get_test_plan_step_or_raise,
)


@pytest.fixture(scope="function")
def new_test_plan(db):
    test_plan = SessionTestPlan(
        name="test plan",
        xctestrun_path="path",
        xctestrun_test_configuration="config",
        repetitions=1,
        repetition_strategy="entire_suite",
        metrics=[Metric.cpu],
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


def test_list_test_plans(new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A database with a test plan

    WHEN: The list_test_plans function is called

    THEN: The function should return a list of test plans
    """

    plans = list_test_plans(session=db)
    assert len(plans) >= 1

    found = False

    for plan in plans:
        test_plan_in_db = new_test_plan
        if plan.id == test_plan_in_db.id:
            assert plan == SessionTestPlanPublic.model_validate(test_plan_in_db)
            found = True
            step = plan.steps[0]
            assert step == SessionTestPlanStepPublic.model_validate(new_test_plan_step)
    assert found


def test_read_test_plan(new_test_plan, db):
    """
    GIVEN: A database with a test plan

    WHEN: The read_test_plan function is called

    THEN: The function should return the test plan
    """
    public_plan = SessionTestPlanPublic.model_validate(new_test_plan)

    assert read_test_plan(session=db, test_plan_id=new_test_plan.id) == public_plan


def test_read_test_plan_not_found(db):
    """
    GIVEN: A database without a test plan

    WHEN: The read_test_plan function is called

    THEN: The function should raise a 404 exception
    """

    with pytest.raises(HTTPException) as e:
        read_test_plan(session=db, test_plan_id=uuid.uuid4())
    assert e.value.status_code == 404


def test_create_test_plan(db):
    """
    GIVEN: A test plan

    WHEN: The create_test_plan function is called

    THEN: The function should return the created test plan
    AND: The test plan should be in the database
    """
    test_plan = SessionTestPlanCreate(
        name="test plan",
        xctestrun_path="path",
        xctestrun_test_configuration="config",
        repetitions=1,
        repetition_strategy="entire_suite",
        metrics=[Metric.cpu],
    )

    created_plan = create_test_plan(session=db, plan=test_plan)

    db_plan = db.exec(
        select(SessionTestPlan).where(SessionTestPlan.id == created_plan.id)
    ).first()

    assert created_plan == SessionTestPlanPublic.model_validate(db_plan)

    assert created_plan.name == test_plan.name
    assert created_plan.xctestrun_path == test_plan.xctestrun_path
    assert (
        created_plan.xctestrun_test_configuration
        == test_plan.xctestrun_test_configuration
    )
    assert created_plan.repetitions == test_plan.repetitions
    assert created_plan.repetition_strategy == test_plan.repetition_strategy
    assert created_plan.metrics == test_plan.metrics


def test_update_test_plan(new_test_plan, db):
    """
    GIVEN: An existing test plan

    WHEN: The update_test_plan function is called

    THEN: The function should return the updated test plan
    AND: The test plan in the database should be updated
    """
    plan_update = SessionTestPlanUpdate(
        name="updated test plan",
    )

    assert new_test_plan.name != plan_update.name

    updated_plan = update_test_plan(
        session=db, plan=plan_update, test_plan_id=new_test_plan.id
    )

    assert updated_plan.name == plan_update.name

    db.refresh(new_test_plan)

    assert new_test_plan.name == plan_update.name
    assert updated_plan == SessionTestPlanPublic.model_validate(new_test_plan)


def test_update_test_plan_not_found(db):
    """
    GIVEN: A database

    WHEN: The update_test_plan function is called with a non-existent test plan id

    THEN: The function should raise a 404 exception
    """
    with pytest.raises(HTTPException) as e:
        update_test_plan(
            session=db,
            test_plan_id=uuid.uuid4(),
            plan=SessionTestPlanUpdate(name="updated test plan"),
        )
    assert e.value.status_code == 404


def test_delete_test_plan(new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A database with a test plan

    WHEN: The delete_test_plan function is called

    THEN: The test plan should be deleted
    """
    delete_test_plan(session=db, test_plan_id=new_test_plan.id)

    plan = db.exec(
        select(SessionTestPlan).where(SessionTestPlan.id == new_test_plan.id)
    ).first()

    assert plan is None


def test_delete_test_plan_not_found(db):
    """
    GIVEN: A database

    WHEN: The delete_test_plan function is called with a non-existent test plan id

    THEN: The function should raise a 404 exception
    """
    with pytest.raises(HTTPException) as e:
        delete_test_plan(session=db, test_plan_id=uuid.uuid4())
    assert e.value.status_code == 404


def test_create_test_plan_step(new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A test plan and a step in the db

    WHEN: The create_test_plan_step function is called with a new step

    THEN: The function should return the created step
    AND: The step should be in the database
    """
    test_plan_step = SessionTestPlanStepCreate(
        name="new step",
        test_plan_id=new_test_plan.id,
        test_cases=["test/case/path"],
    )

    created_step = create_test_plan_step(
        session=db, test_plan_id=new_test_plan.id, step=test_plan_step
    )

    db_step = db.exec(
        select(SessionTestPlanStep).where(SessionTestPlanStep.id == created_step.id)
    ).first()

    assert created_step == SessionTestPlanStepPublic.model_validate(db_step)

    assert created_step.name == test_plan_step.name
    assert created_step.order == 1
    assert created_step.test_cases == test_plan_step.test_cases
    assert created_step.metrics == test_plan_step.metrics
    assert (
        created_step.recording_start_strategy == test_plan_step.recording_start_strategy
    )
    assert created_step.repetitions == test_plan_step.repetitions


def test_create_test_plan_step_no_test_plan(db):
    """
    GIVEN: A database

    WHEN: The create_test_plan_step function is called with a non-existent test plan id

    THEN: The function should raise a 404 exception
    """
    with pytest.raises(HTTPException) as e:
        create_test_plan_step(
            session=db,
            test_plan_id=uuid.uuid4(),
            step=SessionTestPlanStepCreate(
                name="new step", test_cases=["test/case/path"]
            ),
        )
    assert e.value.status_code == 404


def test_update_test_plan_step(new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A test plan and a step in the db

    WHEN: The update_test_plan_step function is called with a new step data

    THEN: The function should return the updated step
    AND: The step should be updated in the database
    """
    step_update = SessionTestPlanStepUpdate(
        name="updated step",
        test_cases=["test/case/path"],
    )

    assert new_test_plan_step.name != step_update.name

    updated_step = update_test_plan_step(
        session=db,
        test_plan_id=new_test_plan.id,
        step_id=new_test_plan_step.id,
        step=step_update,
    )

    assert updated_step.name == step_update.name
    assert updated_step.test_cases == step_update.test_cases

    db.refresh(new_test_plan_step)

    assert new_test_plan_step.name == step_update.name
    assert updated_step == SessionTestPlanStepPublic.model_validate(new_test_plan_step)


def test_update_test_plan_step_not_found(new_test_plan, db):
    """
    GIVEN: A database

    WHEN: The update_test_plan_step function is called with a non-existent step id

    THEN: The function should raise a 404 exception
    """
    with pytest.raises(HTTPException) as e:
        update_test_plan_step(
            session=db,
            test_plan_id=new_test_plan.id,
            step_id=uuid.uuid4(),
            step=SessionTestPlanStepUpdate(name="updated step"),
        )
    assert e.value.status_code == 404


def test_delete_test_plan_step(new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A test plan and a step in the db

    WHEN: The delete_test_plan_step function is called

    THEN: The step should be deleted
    """
    delete_test_plan_step(
        session=db, test_plan_id=new_test_plan.id, step_id=new_test_plan_step.id
    )

    step = db.exec(
        select(SessionTestPlanStep).where(
            SessionTestPlanStep.id == new_test_plan_step.id
        )
    ).first()

    assert step is None


def test_delete_test_plan_step_not_found(new_test_plan, db):
    """
    GIVEN: A test plan and a step in the db

    WHEN: The delete_test_plan_step function is called with a non-existent step id

    THEN: The function should raise a 404 exception
    """
    with pytest.raises(HTTPException) as e:
        delete_test_plan_step(
            session=db, test_plan_id=new_test_plan.id, step_id=uuid.uuid4()
        )
    assert e.value.status_code == 404


def test_reorder_test_plan_steps(new_test_plan, db):
    """
    GIVEN: A test plan with steps

    WHEN: The reorder_test_plan_steps function is called with a new order

    THEN: The steps should be reordered
    """
    steps = [
        SessionTestPlanStepCreate(
            name=f"step {i}",
            test_plan_id=new_test_plan.id,
            test_cases=[f"test/case/path/{i}"],
        )
        for i in range(3)
    ]
    created_steps = [
        create_test_plan_step(session=db, test_plan_id=new_test_plan.id, step=step)
        for step in steps
    ]

    steps_in_order = sorted(created_steps, key=lambda x: x.order)

    new_order = [steps_in_order[1].id, steps_in_order[2].id, steps_in_order[0].id]

    reorder_test_plan_steps(
        session=db,
        test_plan_id=new_test_plan.id,
        step_ids=new_order,
    )

    db.refresh(new_test_plan)

    for step in new_test_plan.steps:
        assert step.order == int(new_order.index(step.id))


def test_reorder_test_plan_steps_duplicate_ids(new_test_plan, db):
    """
    GIVEN: A test plan with a step

    WHEN: The reorder_test_plan_steps function is called with duplicate step ids

    THEN: The function should raise a 400 exception
    """
    step_id = uuid.uuid4()

    with pytest.raises(HTTPException) as e:
        reorder_test_plan_steps(
            session=db,
            test_plan_id=new_test_plan.id,
            step_ids=[step_id, step_id],
        )
    assert e.value.status_code == 400
    assert e.value.detail == "Step ids contain duplicates"


def test_reorder_test_plan_steps_not_found(db):
    """
    GIVEN: A test plan with a step

    WHEN: The reorder_test_plan_steps function is called with a non-existent test plan id

    THEN: The function should raise a 404 exception
    """
    with pytest.raises(HTTPException) as e:
        reorder_test_plan_steps(
            session=db,
            test_plan_id=uuid.uuid4(),
            step_ids=[uuid.uuid4()],
        )
    assert e.value.status_code == 404


def test_reorder_test_plan_steps_id_mismatch(new_test_plan, db):
    """
    GIVEN: A test plan with a step

    WHEN: The reorder_test_plan_steps function is called with a step id that does not belong to the test plan

    THEN: The function should raise a 404 exception
    """
    with pytest.raises(HTTPException) as e:
        reorder_test_plan_steps(
            session=db,
            test_plan_id=new_test_plan.id,
            step_ids=[uuid.uuid4()],
        )
    assert e.value.status_code == 400
    assert e.value.detail == "Step ids mismatch"


@pytest.mark.parametrize(
    "exists",
    [
        True,
        False,
    ],
)
def test_get_test_plan_step(db, new_test_plan, new_test_plan_step, exists):
    """
    GIVEN: A test plan id and a step id

    WHEN: The _get_test_plan_step_or_raise function is called

    THEN: The function should return the step if it exists
    AND: The function should return None if the step does not exist
    """

    if exists:
        step = _get_test_plan_step(
            session=db, test_plan_id=new_test_plan.id, step_id=new_test_plan_step.id
        )
        assert step == new_test_plan_step
    else:
        plan_uuid = uuid.uuid4()
        step_uuid = uuid.uuid4()
        step = _get_test_plan_step(
            session=db, test_plan_id=plan_uuid, step_id=step_uuid
        )
        assert step is None


@pytest.mark.parametrize(
    "exists",
    [
        True,
        False,
    ],
)
def test_get_test_plan_or_raise(exists, new_test_plan, db):
    """
    GIVEN: A test plan id

    WHEN: The _get_test_plan_or_raise function is called

    THEN: The function should return the test plan if it exists
    AND: The function should raise an exception if the test plan does not exist
    """
    if exists:
        plan = _get_test_plan_or_raise(session=db, test_plan_id=new_test_plan.id)
        assert plan == new_test_plan
    else:
        with pytest.raises(HTTPException) as e:
            _get_test_plan_or_raise(session=db, test_plan_id=uuid.uuid4())
        assert e.value.status_code == 404


@pytest.mark.parametrize(
    "exists",
    [
        True,
        False,
    ],
)
def test_get_test_plan_step_or_raise(exists, new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A test plan id and a step id

    WHEN: The _get_test_plan_step_or_raise function is called

    THEN: The function should return the step if it exists
    AND: The function should raise an exception if the step does not exist
    """

    if exists:
        _get_test_plan_step_or_raise(
            session=db, test_plan_id=new_test_plan.id, step_id=new_test_plan_step.id
        )
    else:
        plan_uuid = uuid.uuid4()
        step_uuid = uuid.uuid4()
        with pytest.raises(HTTPException) as e:
            _get_test_plan_step_or_raise(
                session=db, test_plan_id=plan_uuid, step_id=step_uuid
            )
        assert e.value.status_code == 404
