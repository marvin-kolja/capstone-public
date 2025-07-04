import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.custom_responses import build_common_http_exception_responses
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
from api.depends import AsyncSessionDep
from api.services import api_test_plan_service, project_service

router = APIRouter(prefix="/test-plans", tags=["testPlans"])


@router.get("/", responses=build_common_http_exception_responses([422, 500]))
async def list_test_plans(
    *, session: AsyncSessionDep, project_id: Optional[uuid.UUID] = None
) -> list[SessionTestPlanPublic]:
    """
    List user created test plans.
    """
    return await api_test_plan_service.list_test_plans(
        session=session, project_id=project_id
    )


@router.post("/", responses=build_common_http_exception_responses([400, 422, 500]))
async def create_test_plan(
    *, session: AsyncSessionDep, test_plan: SessionTestPlanCreate
) -> SessionTestPlanPublic:
    """
    Create a new test plan.
    """
    project = await project_service.read_project(
        session=session, project_id=test_plan.project_id
    )
    if project is None:
        raise HTTPException(status_code=400, detail="Invalid project id")

    build = await project_service.read_build(
        session=session, build_id=test_plan.build_id
    )

    if build is None or build.project_id != project.id:
        raise HTTPException(status_code=400, detail="Invalid build id")

    return await api_test_plan_service.create_test_plan(session=session, plan=test_plan)


@router.get(
    "/{test_plan_id}", responses=build_common_http_exception_responses([404, 422, 500])
)
async def read_test_plan(
    *, session: AsyncSessionDep, test_plan_id: uuid.UUID
) -> SessionTestPlanPublic:
    """
    Get a test plan.
    """
    return await _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)


@router.patch(
    "/{test_plan_id}",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def update_test_plan(
    *, session: AsyncSessionDep, test_plan_id: uuid.UUID, plan: SessionTestPlanUpdate
) -> SessionTestPlanPublic:
    """
    Update a test plan.
    """
    db_plan = await _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    project = await project_service.read_project(
        session=session, project_id=db_plan.project_id
    )
    if project is None:
        raise HTTPException(status_code=500)

    return await api_test_plan_service.update_test_plan(
        session=session, db_plan=db_plan, plan=plan
    )


@router.delete(
    "/{test_plan_id}", responses=build_common_http_exception_responses([404, 422, 500])
)
async def delete_test_plan(
    *, session: AsyncSessionDep, test_plan_id: uuid.UUID
) -> None:
    """
    Delete a test plan.
    """
    db_plan = await _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    return await api_test_plan_service.delete_test_plan(
        session=session, db_plan=db_plan
    )


@router.post(
    "/{test_plan_id}/steps",
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def create_test_plan_step(
    *,
    session: AsyncSessionDep,
    test_plan_id: uuid.UUID,
    step: SessionTestPlanStepCreate
) -> SessionTestPlanStepPublic:
    """
    Create a new step in a test plan.
    """
    db_plan = await _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    return await api_test_plan_service.create_test_plan_step(
        session=session, db_plan=db_plan, step=step
    )


@router.patch(
    "/{test_plan_id}/steps/{step_id}",
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def update_test_plan_step(
    *,
    session: AsyncSessionDep,
    test_plan_id: uuid.UUID,
    step_id: uuid.UUID,
    step: SessionTestPlanStepUpdate
) -> SessionTestPlanStepPublic:
    """
    Update a step in a test plan.
    """
    db_step = await _get_test_plan_step_or_raise(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )

    return await api_test_plan_service.update_test_plan_step(
        session=session, db_step=db_step, step=step
    )


@router.delete(
    "/{test_plan_id}/steps/{step_id}",
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def delete_test_plan_step(
    *, session: AsyncSessionDep, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> None:
    """
    Delete a step in a test plan.
    """
    db_step = await _get_test_plan_step_or_raise(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )

    return await api_test_plan_service.delete_test_plan_step(
        session=session, db_step=db_step
    )


@router.post(
    "/{test_plan_id}/steps/reorder",
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def reorder_test_plan_steps(
    *, session: AsyncSessionDep, test_plan_id: uuid.UUID, step_ids: list[uuid.UUID]
) -> None:
    """
    Reorder steps in a test plan.
    """
    db_plan = await _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    return await api_test_plan_service.reorder_test_plan_steps(
        session=session, db_plan=db_plan, step_ids=step_ids
    )


async def _get_test_plan_or_raise(
    *, session: AsyncSession, test_plan_id: uuid.UUID
) -> SessionTestPlan:
    """
    Get a test plan by id.

    :raises HTTPException: If the test plan is not found
    """
    db_plan = await api_test_plan_service.read_test_plan(
        session=session, test_plan_id=test_plan_id
    )
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Test plan not found")
    return db_plan


async def _get_test_plan_step_or_raise(
    *, session: AsyncSession, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> SessionTestPlanStep:
    """
    Get a test plan step by id.

    :raises HTTPException: If the test plan is not found
    """
    db_step = await api_test_plan_service.read_test_plan_step(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )
    if db_step is None:
        raise HTTPException(status_code=404, detail="Test plan step not found")
    return db_step
