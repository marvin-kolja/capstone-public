import uuid

import pytest
from core.test_session.metrics import Metric
from fastapi.exceptions import RequestValidationError
from sqlmodel import select

from api.models import (
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
    read_test_plan_step,
)


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
    assert read_test_plan(session=db, test_plan_id=new_test_plan.id) == new_test_plan


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

    updated_plan = update_test_plan(session=db, plan=plan_update, db_plan=new_test_plan)

    assert updated_plan.name == plan_update.name

    db.refresh(new_test_plan)

    assert new_test_plan.name == plan_update.name
    assert updated_plan == SessionTestPlanPublic.model_validate(new_test_plan)


def test_delete_test_plan(new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A database with a test plan

    WHEN: The delete_test_plan function is called

    THEN: The test plan should be deleted from the DB
    AND: The test plan steps should be deleted from the DB
    """
    delete_test_plan(session=db, db_plan=new_test_plan)

    plan = db.exec(
        select(SessionTestPlan).where(SessionTestPlan.id == new_test_plan.id)
    ).first()

    assert plan is None

    steps = db.exec(
        select(SessionTestPlanStep).where(
            SessionTestPlanStep.test_plan_id == new_test_plan.id
        )
    ).all()

    assert len(steps) == 0


def test_create_test_plan_step(new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A test plan and a step in the db

    WHEN: The create_test_plan_step function is called with a new step

    THEN: The function should return the created step
    AND: The step should be in the database
    """
    test_plan_step = SessionTestPlanStepCreate(
        name="new step",
        test_cases=["test/case/path"],
    )

    created_step = create_test_plan_step(
        session=db, db_plan=new_test_plan, step=test_plan_step
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
        db_step=new_test_plan_step,
        step=step_update,
    )

    assert updated_step.name == step_update.name
    assert updated_step.test_cases == step_update.test_cases

    db.refresh(new_test_plan_step)

    assert new_test_plan_step.name == step_update.name
    assert updated_step == SessionTestPlanStepPublic.model_validate(new_test_plan_step)


def test_delete_test_plan_step(new_test_plan, new_test_plan_step, db):
    """
    GIVEN: A test plan and a step in the db

    WHEN: The delete_test_plan_step function is called

    THEN: The step should be deleted
    """
    delete_test_plan_step(
        session=db,
        db_step=new_test_plan_step,
    )

    step = db.exec(
        select(SessionTestPlanStep).where(
            SessionTestPlanStep.id == new_test_plan_step.id
        )
    ).first()

    assert step is None


def test_reorder_test_plan_steps(new_test_plan, db):
    """
    GIVEN: A test plan with steps

    WHEN: The reorder_test_plan_steps function is called with a new order

    THEN: The steps should be reordered
    """
    steps = [
        SessionTestPlanStepCreate(
            name=f"step {i}",
            test_cases=[f"test/case/path/{i}"],
        )
        for i in range(3)
    ]
    created_steps = [
        create_test_plan_step(session=db, db_plan=new_test_plan, step=step)
        for step in steps
    ]

    steps_in_order = sorted(created_steps, key=lambda x: x.order)

    new_order = [steps_in_order[1].id, steps_in_order[2].id, steps_in_order[0].id]

    reorder_test_plan_steps(
        session=db,
        db_plan=new_test_plan,
        step_ids=new_order,
    )

    db.refresh(new_test_plan)

    for step in new_test_plan.steps:
        assert step.order == int(new_order.index(step.id))


def test_reorder_test_plan_steps_duplicate_ids(new_test_plan, db):
    """
    GIVEN: A test plan with a step

    WHEN: The reorder_test_plan_steps function is called with duplicate step ids

    THEN: The function should raise a RequestValidationError
    """
    step_id = uuid.uuid4()

    with pytest.raises(RequestValidationError) as e:
        reorder_test_plan_steps(
            session=db,
            db_plan=new_test_plan,
            step_ids=[step_id, step_id],
        )


def test_reorder_test_plan_steps_id_mismatch(new_test_plan, db):
    """
    GIVEN: A test plan with a step

    WHEN: The reorder_test_plan_steps function is called with a step ids that do not belong to the test plan

    THEN: The function should raise a RequestValidationError
    """
    with pytest.raises(RequestValidationError) as e:
        reorder_test_plan_steps(
            session=db,
            db_plan=new_test_plan,
            step_ids=[uuid.uuid4()],
        )


@pytest.mark.parametrize(
    "exists",
    [
        True,
        False,
    ],
)
def test_read_test_plan_step(db, new_test_plan, new_test_plan_step, exists):
    """
    GIVEN: A test plan id and a step id

    WHEN: The read_test_plan_step function is called

    THEN: The function should return the step if it exists
    AND: The function should return None if the step does not exist
    """

    if exists:
        step = read_test_plan_step(
            session=db, test_plan_id=new_test_plan.id, step_id=new_test_plan_step.id
        )
        assert step == new_test_plan_step
    else:
        plan_uuid = uuid.uuid4()
        step_uuid = uuid.uuid4()
        step = read_test_plan_step(
            session=db, test_plan_id=plan_uuid, step_id=step_uuid
        )
        assert step is None
