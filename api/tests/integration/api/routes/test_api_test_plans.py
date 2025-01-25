import uuid

from core.test_session.metrics import Metric
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


def test_list_test_plans(new_test_plan, new_test_plan_step, client):
    """
    GIVEN: A test plan in the database

    WHEN: GETing the `/test-plans/` endpoint

    THEN: The response should contain a list of test plans with the test plan from the database
    """
    r = client.get("/test-plans/")

    assert r.status_code == 200

    assert len(r.json()) >= 1

    plans = [SessionTestPlanPublic.model_validate(plan) for plan in r.json()]

    found = False

    for plan in plans:
        test_plan_in_db = new_test_plan
        if plan.id == test_plan_in_db.id:
            assert plan == SessionTestPlanPublic.model_validate(test_plan_in_db)
            found = True
            step = plan.steps[0]
            assert step == SessionTestPlanStepPublic.model_validate(new_test_plan_step)
    assert found


def test_read_test_plan(new_test_plan, client):
    """
    GIVEN: A test plan in the database

    WHEN: GETing the `/test-plans/{id}` endpoint

    THEN: The response should contain the test plan
    """
    r = client.get(f"/test-plans/{new_test_plan.id}")

    assert r.status_code == 200

    assert SessionTestPlanPublic.model_validate(
        r.json()
    ) == SessionTestPlanPublic.model_validate(new_test_plan)


def test_read_test_plan_not_found(client):
    """
    GIVEN: no test plan in the database

    WHEN: GETing the `/test-plans/{id}` endpoint

    THEN: The response should be a 404
    """
    r = client.get(f"/test-plans/{uuid.uuid4().hex}")

    assert r.status_code == 404


def test_create_test_plan(client, db, new_db_project):
    """
    GIVEN: A test plan creation model

    WHEN: POSTing to the `/test-plans/` endpoint

    THEN: The response should contain the created test plan
    AND: The test plan should be in the database
    """
    test_plan = SessionTestPlanCreate(
        name="test plan",
        xc_test_plan_name=new_db_project.schemes[0].xc_test_plans[0].name,
        repetitions=1,
        repetition_strategy="entire_suite",
        metrics=[Metric.cpu],
        project_id=new_db_project.id.hex,
    )

    r = client.post("/test-plans/", json=test_plan.model_dump(mode="json"))

    assert r.status_code == 200

    created_plan = SessionTestPlanPublic.model_validate(r.json())

    db_plan = db.exec(
        select(SessionTestPlan).where(SessionTestPlan.id == created_plan.id)
    ).first()

    assert created_plan == SessionTestPlanPublic.model_validate(db_plan)

    assert created_plan.name == test_plan.name
    assert created_plan.xc_test_plan_name == test_plan.xc_test_plan_name
    assert created_plan.project_id == test_plan.project_id == test_plan.project_id
    assert created_plan.repetitions == test_plan.repetitions
    assert created_plan.repetition_strategy == test_plan.repetition_strategy
    assert created_plan.metrics == test_plan.metrics


def test_create_test_plan_invalid_project(client, db):
    """
    GIVEN: A test plan creation model with an invalid project id

    WHEN: POSTing to the `/test-plans/` endpoint

    THEN: The response should be a 400
    """
    r = client.post(
        "/test-plans/",
        json=SessionTestPlanCreate(
            name="test plan",
            xc_test_plan_name="test plan",
            repetitions=1,
            repetition_strategy="entire_suite",
            metrics=[Metric.cpu],
            project_id=uuid.uuid4(),
        ).model_dump(mode="json"),
    )

    assert r.status_code == 400


def test_create_test_plan_invalid_xc_test_plan(client, db, new_db_project):
    """
    GIVEN: A test plan creation model with an invalid xc test plan name

    WHEN: POSTing to the `/test-plans/` endpoint

    THEN: The response should be a 400
    """
    r = client.post(
        "/test-plans/",
        json=SessionTestPlanCreate(
            name="test plan",
            xc_test_plan_name="invalid test plan",
            repetitions=1,
            repetition_strategy="entire_suite",
            metrics=[Metric.cpu],
            project_id=new_db_project.id,
        ).model_dump(mode="json"),
    )

    assert r.status_code == 400


def test_update_test_plan(new_test_plan, db, client):
    """
    GIVEN: An existing test plan in the database

    WHEN: PATHing `/test-plans/{id}` endpoint

    THEN: The response should contain the updated test plan
    AND: The test plan in the database should be updated
    """
    plan_update = SessionTestPlanUpdate(
        name="updated test plan",
    )

    assert new_test_plan.name != plan_update.name

    r = client.patch(
        f"/test-plans/{new_test_plan.id}",
        json=plan_update.model_dump(exclude_unset=True),
    )

    print(r.text)

    assert r.status_code == 200

    updated_plan = SessionTestPlanPublic.model_validate(r.json())

    assert updated_plan.name == plan_update.name

    db.refresh(new_test_plan)

    assert new_test_plan.name == plan_update.name
    assert updated_plan == SessionTestPlanPublic.model_validate(new_test_plan)


def test_update_test_plan_not_found(client):
    """
    GIVEN: no test plan in the database

    WHEN: PATCHing `/test-plans/{id}` endpoint

    THEN: The response should be a 404
    """
    r = client.patch(
        f"/test-plans/{uuid.uuid4()}",
        json=SessionTestPlanUpdate(name="updated test plan").model_dump(
            exclude_unset=True
        ),
    )

    assert r.status_code == 404


def test_update_test_plan_invalid_xc_test_plan(client, new_test_plan):
    """
    GIVEN: A test plan in the database

    WHEN: PATCHing `/test-plans/{id}` endpoint with an invalid xc test plan name

    THEN: The response should be a 400
    """
    r = client.patch(
        f"/test-plans/{new_test_plan.id}",
        json=SessionTestPlanUpdate(xc_test_plan_name="invalid test plan").model_dump(
            exclude_unset=True
        ),
    )

    assert r.status_code == 400


def test_delete_test_plan(new_test_plan, new_test_plan_step, db, client):
    """
    GIVEN: A test plan in the database

    WHEN: DELETEing the `/test-plans/{id}` endpoint

    THEN: The test plan should be deleted from the DB
    AND: The test plan steps should be deleted from the DB
    """
    r = client.delete(f"/test-plans/{new_test_plan.id}")
    assert r.status_code == 200

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


def test_delete_test_plan_not_found(client):
    """
    GIVEN: no test plan in the database

    WHEN: DELETEing the `/test-plans/{id}` endpoint

    THEN: The response should be a 404
    """
    r = client.delete(f"/test-plans/{uuid.uuid4().hex}")
    assert r.status_code == 404


def test_create_test_plan_step(new_test_plan, new_test_plan_step, db, client):
    """
    GIVEN: A test plan and a step in the db

    WHEN: POSTing to the `/test-plans/{id}/steps` endpoint

    THEN: The response should contain the created step
    AND: The step should be in the database
    """
    test_plan_step = SessionTestPlanStepCreate(
        name="new step",
        test_cases=["test/case/path"],
    )

    r = client.post(
        f"/test-plans/{new_test_plan.id}/steps",
        json=test_plan_step.model_dump(),
    )

    assert r.status_code == 200

    created_step = SessionTestPlanStepPublic.model_validate(r.json())

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


def test_create_test_plan_step_invalid_test_cases(client, new_test_plan):
    """
    GIVEN: A test plan in the db

    WHEN: POSTing to the `/test-plans/{id}/steps` endpoint with invalid test cases

    THEN: The response should be a 422
    """
    r = client.post(
        f"/test-plans/{new_test_plan.id}/steps",
        json=SessionTestPlanStepCreate(
            name="new step",
            test_cases=["target/test_case/path", "invalid_target/test_case/path"],
        ).model_dump(),
    )

    assert r.status_code == 422
    assert r.json()["detail"][0]["msg"] == "Invalid test case path"


def test_create_test_plan_step_no_test_plan(client):
    """
    GIVEN: No test plan in the database

    WHEN: POSTing to the `/test-plans/{id}/steps` endpoint

    THEN: The response should be a 404
    """
    r = client.post(
        f"/test-plans/{uuid.uuid4()}/steps",
        json=SessionTestPlanStepCreate(name="new step", test_cases=[""]).model_dump(),
    )
    assert r.status_code == 404


def test_update_test_plan_step(new_test_plan, new_test_plan_step, db, client):
    """
    GIVEN: A test plan and a step in the db

    WHEN: PATCHing the `/test-plans/{id}/steps/{id}` endpoint

    THEN: The response should contain the updated step
    AND: The step should be updated in the database
    """
    step_update = SessionTestPlanStepUpdate(
        name="updated step",
        test_cases=["test/case/path"],
    )

    assert new_test_plan_step.name != step_update.name

    r = client.patch(
        f"/test-plans/{new_test_plan.id}/steps/{new_test_plan_step.id}",
        json=step_update.model_dump(exclude_unset=True),
    )

    assert r.status_code == 200

    updated_step = SessionTestPlanStepPublic.model_validate(r.json())

    assert updated_step.name == step_update.name
    assert updated_step.test_cases == step_update.test_cases

    db.refresh(new_test_plan_step)

    assert new_test_plan_step.name == step_update.name
    assert updated_step == SessionTestPlanStepPublic.model_validate(new_test_plan_step)


def test_update_test_plan_step_invalid_test_cases(
    client, new_test_plan, new_test_plan_step
):
    """
    GIVEN: A test plan and a step in the db

    WHEN: PATCHing the `/test-plans/{id}/steps/{id}` endpoint with invalid test cases

    THEN: The response should be a 422
    """
    r = client.patch(
        f"/test-plans/{new_test_plan.id}/steps/{new_test_plan_step.id}",
        json=SessionTestPlanStepUpdate(
            name="updated step", test_cases=["invalid"]
        ).model_dump(exclude_unset=True),
    )

    assert r.status_code == 422
    assert r.json()["detail"][0]["msg"] == "Invalid test case path"


def test_update_test_plan_step_not_found(new_test_plan, client):
    """
    GIVEN: A test plan in the db, but no matching step

    WHEN: PATCHing the `/test-plans/{id}/steps/{id}` endpoint

    THEN: The response should be a 404
    """
    r = client.patch(
        f"/test-plans/{new_test_plan.id}/steps/{uuid.uuid4()}",
        json=SessionTestPlanStepUpdate(name="updated step").model_dump(
            exclude_unset=True
        ),
    )

    assert r.status_code == 404


def test_delete_test_plan_step(new_test_plan, new_test_plan_step, db, client):
    """
    GIVEN: A test plan and a step in the db

    WHEN: DELETEing the `/test-plans/{id}/steps/{id}` endpoint

    THEN: The step should be deleted from the DB
    """
    r = client.delete(f"/test-plans/{new_test_plan.id}/steps/{new_test_plan_step.id}")

    assert r.status_code == 200

    step = db.exec(
        select(SessionTestPlanStep).where(
            SessionTestPlanStep.id == new_test_plan_step.id
        )
    ).first()

    assert step is None


def test_delete_test_plan_step_not_found(new_test_plan, client):
    """
    GIVEN: A test plan, but no step in the db

    WHEN: DELETEing the `/test-plans/{id}/steps/{id}` endpoint

    THEN: The response should be a 404
    """
    r = client.delete(f"/test-plans/{new_test_plan.id}/steps/{uuid.uuid4().hex}")
    assert r.status_code == 404


def test_reorder_test_plan_steps(new_test_plan, db, client):
    """
    GIVEN: A test plan with steps in the db

    WHEN: POSTing to the `/test-plans/{id}/steps/reorder` endpoint

    THEN: The steps should be reordered
    """
    steps = [
        SessionTestPlanStepCreate(
            name=f"step {i}",
            test_cases=[f"test/case/path{i}"],
        )
        for i in range(3)
    ]

    created_steps = [
        SessionTestPlanStepPublic.model_validate(
            client.post(
                f"/test-plans/{new_test_plan.id.hex}/steps",
                json=step.model_dump(),
            ).json()
        )
        for step in steps
    ]

    steps_in_order = sorted(created_steps, key=lambda x: x.order)

    new_order = [steps_in_order[1].id, steps_in_order[2].id, steps_in_order[0].id]

    r = client.post(
        f"/test-plans/{new_test_plan.id.hex}/steps/reorder",
        json=[str(_id) for _id in new_order],
    )

    assert r.status_code == 200

    db.refresh(new_test_plan)

    for step in new_test_plan.steps:
        assert step.order == int(new_order.index(step.id))


def test_reorder_test_plan_steps_duplicate_ids(new_test_plan, client):
    """
    GIVEN: A test plan in the db

    WHEN: POSTing to the `/test-plans/{id}/steps/reorder` endpoint with duplicate step ids

    THEN: The response should be a 422
    """
    step_id = uuid.uuid4()

    r = client.post(
        f"/test-plans/{new_test_plan.id}/steps/reorder",
        json=[str(step_id), str(step_id)],
    )

    assert r.status_code == 422
    assert r.json()["detail"][0]["msg"] == "Step ids contain duplicates"


def test_reorder_test_plan_steps_not_found(client):
    """
    GIVEN: No test plan in the db

    WHEN: POSTing to the `/test-plans/{id}/steps/reorder` endpoint

    THEN: The response should be a 404
    """
    r = client.post(
        f"/test-plans/{uuid.uuid4()}/steps/reorder",
        json=[str(uuid.uuid4())],
    )
    assert r.status_code == 404


def test_reorder_test_plan_steps_id_mismatch(new_test_plan, new_test_plan_step, client):
    """
    GIVEN: A test plan and a step in the db

    WHEN: POSTing to the `/test-plans/{id}/steps/reorder` endpoint with a mismatched step id

    THEN: The response should be a 422
    """
    r = client.post(
        f"/test-plans/{new_test_plan.id}/steps/reorder",
        json=[str(uuid.uuid4())],
    )

    assert r.status_code == 422
    assert r.json()["detail"][0]["msg"] == "Step ids mismatch"
