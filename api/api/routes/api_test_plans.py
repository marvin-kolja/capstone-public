import uuid

from fastapi import APIRouter

from api.db_models import (
    SessionTestPlanCreate,
    SessionTestPlanPublic,
    SessionTestPlanUpdate,
    SessionTestPlanStepPublic,
    SessionTestPlanStepCreate,
    SessionTestPlanStepUpdate,
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
    return api_test_plan_service.read_test_plan(
        session=session, test_plan_id=test_plan_id
    )


@router.patch("/{test_plan_id}")
async def update_test_plan(
    *, session: SessionDep, test_plan_id: uuid.UUID, plan: SessionTestPlanUpdate
) -> SessionTestPlanPublic:
    """
    Update a test plan.
    """
    return api_test_plan_service.update_test_plan(
        session=session, test_plan_id=test_plan_id, plan=plan
    )


@router.delete("/{test_plan_id}")
async def delete_test_plan(*, session: SessionDep, test_plan_id: uuid.UUID) -> None:
    """
    Delete a test plan.
    """
    return api_test_plan_service.delete_test_plan(
        session=session, test_plan_id=test_plan_id
    )


@router.post("/{test_plan_id}/steps")
async def create_test_plan_step(
    *, session: SessionDep, test_plan_id: uuid.UUID, step: SessionTestPlanStepCreate
) -> SessionTestPlanStepPublic:
    """
    Create a new step in a test plan.
    """
    return api_test_plan_service.create_test_plan_step(
        session=session, test_plan_id=test_plan_id, step=step
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
    return api_test_plan_service.update_test_plan_step(
        session=session, test_plan_id=test_plan_id, step_id=step_id, step=step
    )


@router.delete("/{test_plan_id}/steps/{step_id}")
async def delete_test_plan_step(
    *, session: SessionDep, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> None:
    """
    Delete a step in a test plan.
    """
    return api_test_plan_service.delete_test_plan_step(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )


@router.post("/{test_plan_id}/steps/reorder")
async def reorder_test_plan_steps(
    *, session: SessionDep, test_plan_id: uuid.UUID, step_ids: list[uuid.UUID]
) -> None:
    """
    Reorder steps in a test plan.
    """
    return api_test_plan_service.reorder_test_plan_steps(
        session=session, test_plan_id=test_plan_id, step_ids=step_ids
    )
