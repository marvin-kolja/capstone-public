from sqlalchemy import text
from sqlmodel import select

from api.models import SessionTestPlan, SessionTestPlanStep, RepetitionStrategy


def test_session_test_plan_cascade_deletion(db, new_db_project):
    """
    GIVEN: A test plan with test steps

    WHEN: The test plan is deleted not using SQLAlchemy ORM

    THEN: The test cases are also deleted using SQL cascade deletion
    """
    # Create a test plan with test steps
    test_plan = SessionTestPlan(
        name="Test Plan 1",
        xc_test_plan_name=new_db_project.schemes[0].xc_test_plans[0].name,
        repetitions=1,
        repetition_strategy=RepetitionStrategy.entire_suite,
        project_id=new_db_project.id,
        metrics=[],
    )
    db.add(test_plan)
    db.commit()
    db.refresh(test_plan)

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
    db.commit()

    # Delete the test plan
    # noinspection SqlResolve
    db.execute(
        text("DELETE FROM session_testplan WHERE id=:plan_id;"),
        {"plan_id": test_plan_id.hex},
    )

    # Check if the test steps are deleted
    db_plan = db.get(SessionTestPlan, test_plan_id)
    assert db_plan is None

    # Check if the test plan is deleted
    db_steps = db.exec(
        select(SessionTestPlanStep).where(
            SessionTestPlanStep.test_plan_id == test_plan_id
        )
    ).all()
    assert db_steps == []
