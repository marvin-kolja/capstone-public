import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from api.models import (
    SessionTestPlanCreate,
    SessionTestPlanPublic,
    SessionTestPlanUpdate,
    SessionTestPlanStepPublic,
    SessionTestPlanStepCreate,
    SessionTestPlanStepUpdate,
    SessionTestPlan,
    SessionTestPlanStep,
)
from api.depends import SessionDep
from api.services import api_test_plan_service

router = APIRouter(prefix="/test-plans", tags=["testPlans"])


@router.get("/")
async def list_test_plans(*, session: SessionDep) -> list[SessionTestPlanPublic]:
    """
    List user created test plans.
    """
    return api_test_plan_service.list_test_plans(session=session)


@router.post("/")
async def create_test_plan(
    *, session: SessionDep, test_plan: SessionTestPlanCreate
) -> SessionTestPlanPublic:
    """
    Create a new test plan.
    """
    return api_test_plan_service.create_test_plan(session=session, plan=test_plan)


@router.get("/{test_plan_id}")
async def read_test_plan(
    *, session: SessionDep, test_plan_id: uuid.UUID
) -> SessionTestPlanPublic:
    """
    Get a test plan.
    """
    return _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)


@router.patch("/{test_plan_id}")
async def update_test_plan(
    *, session: SessionDep, test_plan_id: uuid.UUID, plan: SessionTestPlanUpdate
) -> SessionTestPlanPublic:
    """
    Update a test plan.
    """
    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    return api_test_plan_service.update_test_plan(
        session=session, db_plan=db_plan, plan=plan
    )


@router.delete("/{test_plan_id}")
async def delete_test_plan(*, session: SessionDep, test_plan_id: uuid.UUID) -> None:
    """
    Delete a test plan.
    """
    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    return api_test_plan_service.delete_test_plan(session=session, db_plan=db_plan)


@router.post("/{test_plan_id}/steps")
async def create_test_plan_step(
    *, session: SessionDep, test_plan_id: uuid.UUID, step: SessionTestPlanStepCreate
) -> SessionTestPlanStepPublic:
    """
    Create a new step in a test plan.
    """
    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    return api_test_plan_service.create_test_plan_step(
        session=session, db_plan=db_plan, step=step
    )


@router.patch("/{test_plan_id}/steps/{step_id}")
async def update_test_plan_step(
    *,
    session: SessionDep,
    test_plan_id: uuid.UUID,
    step_id: uuid.UUID,
    step: SessionTestPlanStepUpdate
) -> SessionTestPlanStepPublic:
    """
    Update a step in a test plan.
    """
    db_step = _get_test_plan_step_or_raise(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )

    return api_test_plan_service.update_test_plan_step(
        session=session, db_step=db_step, step=step
    )


@router.delete("/{test_plan_id}/steps/{step_id}")
async def delete_test_plan_step(
    *, session: SessionDep, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> None:
    """
    Delete a step in a test plan.
    """
    db_step = _get_test_plan_step_or_raise(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )

    return api_test_plan_service.delete_test_plan_step(session=session, db_step=db_step)


@router.post("/{test_plan_id}/steps/reorder")
async def reorder_test_plan_steps(
    *, session: SessionDep, test_plan_id: uuid.UUID, step_ids: list[uuid.UUID]
) -> None:
    """
    Reorder steps in a test plan.
    """
    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    return api_test_plan_service.reorder_test_plan_steps(
        session=session, db_plan=db_plan, step_ids=step_ids
    )


def _get_test_plan_or_raise(
    *, session: Session, test_plan_id: uuid.UUID
) -> SessionTestPlan:
    """
    Get a test plan by id.

    :raises HTTPException: If the test plan is not found
    """
    db_plan = api_test_plan_service.read_test_plan(
        session=session, test_plan_id=test_plan_id
    )
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Test plan not found")
    return db_plan


def _get_test_plan_step_or_raise(
    *, session: Session, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> SessionTestPlanStep:
    """
    Get a test plan step by id.

    :raises HTTPException: If the test plan is not found
    """
    db_step = api_test_plan_service.read_test_plan_step(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )
    if db_step is None:
        raise HTTPException(status_code=404, detail="Test plan step not found")
    return db_step
