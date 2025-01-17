import pytest
from core.test_session.metrics import Metric

from api.models import SessionTestPlanStep, SessionTestPlan


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
