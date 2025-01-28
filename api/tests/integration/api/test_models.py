import pytest
from sqlalchemy import text
from sqlmodel import select

from api.models import SessionTestPlan, SessionTestPlanStep, RepetitionStrategy


@pytest.mark.asyncio
async def test_session_test_plan_cascade_deletion(
    db, new_db_project, new_db_fake_build
):
    """
    GIVEN: A test plan with test steps

    WHEN: The test plan is deleted not using SQLAlchemy ORM

    THEN: The test cases are also deleted using SQL cascade deletion
    """
    # Create a test plan with test steps
    test_plan = SessionTestPlan(
        name="Test Plan 1",
        build_id=new_db_fake_build.id,
        repetitions=1,
        repetition_strategy=RepetitionStrategy.entire_suite,
        project_id=new_db_project.id,
        metrics=[],
    )
    db.add(test_plan)
    await db.commit()
    await db.refresh(test_plan)

    test_plan_id = test_plan.id

    test_step_1 = SessionTestPlanStep(
        order=0,
        name="Test Step 1",
        test_cases=["test/case/path"],
        test_plan_id=test_plan.id,
    )
    test_step_2 = SessionTestPlanStep(
        order=1,
        name="Test Step 2",
        test_cases=["test/case/path"],
        test_plan_id=test_plan.id,
    )
    db.add(test_step_1)
    db.add(test_step_2)
    await db.commit()

    # Delete the test plan
    # noinspection SqlResolve
    await db.execute(
        text("DELETE FROM session_testplan WHERE id=:plan_id;"),
        {"plan_id": test_plan_id.hex},
    )

    db.expire_all()

    # Check if the test steps are deleted
    db_plan = await db.get(SessionTestPlan, test_plan_id)
    assert db_plan is None

    # Check if the test plan is deleted
    db_steps = (
        (
            await db.execute(
                select(SessionTestPlanStep).where(
                    SessionTestPlanStep.test_plan_id == test_plan_id
                )
            )
        )
        .scalars()
        .all()
    )
    assert db_steps == []
