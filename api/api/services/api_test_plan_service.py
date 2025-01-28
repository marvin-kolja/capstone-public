import logging
import uuid
from typing import Optional

from core.test_session import plan as core_plan
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.models import (
    SessionTestPlan,
    SessionTestPlanPublic,
    SessionTestPlanCreate,
    SessionTestPlanStep,
    SessionTestPlanUpdate,
    SessionTestPlanStepCreate,
    SessionTestPlanStepUpdate,
    SessionTestPlanStepPublic,
)
from api.services.helpers import update_db_model

logger = logging.getLogger(__name__)


async def list_test_plans(
    *, session: AsyncSession, project_id: Optional[uuid.UUID] = None
) -> list[SessionTestPlanPublic]:
    statement = select(SessionTestPlan)
    if project_id:
        statement = statement.where(SessionTestPlan.project_id == project_id)

    plans = (await session.execute(statement)).scalars().all()
    return [SessionTestPlanPublic.model_validate(plan) for plan in plans]


async def create_test_plan(
    *, session: AsyncSession, plan: SessionTestPlanCreate
) -> SessionTestPlanPublic:
    db_plan = SessionTestPlan.model_validate(plan)
    session.add(db_plan)
    await session.commit()
    await session.refresh(db_plan)
    return SessionTestPlanPublic.model_validate(db_plan)


async def read_test_plan(
    *, session: AsyncSession, test_plan_id: uuid.UUID
) -> Optional[SessionTestPlan]:
    statement = select(SessionTestPlan).where(SessionTestPlan.id == test_plan_id)
    res = await session.execute(statement)
    db_plan = res.scalar_one_or_none()
    if db_plan is None:
        return None
    return db_plan


async def update_test_plan(
    *, session: AsyncSession, db_plan: SessionTestPlan, plan: SessionTestPlanUpdate
) -> SessionTestPlanPublic:
    update_db_model(db_model=db_plan, new_data_model=plan)
    session.add(db_plan)
    await session.commit()
    await session.refresh(db_plan)
    return SessionTestPlanPublic.model_validate(db_plan)


async def delete_test_plan(*, session: AsyncSession, db_plan: SessionTestPlan):
    await session.delete(db_plan)
    await session.commit()
    return


async def create_test_plan_step(
    *, session: AsyncSession, db_plan: SessionTestPlan, step: SessionTestPlanStepCreate
) -> SessionTestPlanStepPublic:
    db_step = SessionTestPlanStep.model_validate(
        {
            **step.model_dump(),
            "test_plan_id": db_plan.id,
            "order": len(db_plan.steps),
        }
    )
    _validate_test_cases(db_step.test_cases)
    db_plan.steps.append(db_step)
    session.add(db_plan)
    await session.commit()
    await session.refresh(db_plan)
    return SessionTestPlanStepPublic.model_validate(db_step)


async def update_test_plan_step(
    *,
    session: AsyncSession,
    db_step: SessionTestPlanStep,
    step: SessionTestPlanStepUpdate,
) -> SessionTestPlanStepPublic:
    update_db_model(db_model=db_step, new_data_model=step)
    _validate_test_cases(db_step.test_cases)
    session.add(db_step)
    await session.commit()
    await session.refresh(db_step)
    return SessionTestPlanStepPublic.model_validate(db_step)


async def delete_test_plan_step(*, session: AsyncSession, db_step: SessionTestPlanStep):
    await session.delete(db_step)

    await session.flush()  # Flush to separate the deletion from the reordering

    # Reorder the remaining steps to fill the gap left by the deleted step
    remaining_steps_statements = select(SessionTestPlanStep).where(
        SessionTestPlanStep.test_plan_id == db_step.test_plan_id
    )
    remaining_steps = (
        (await session.execute(remaining_steps_statements)).scalars().all()
    )

    # Assign temporary order to all remaining steps to avoid unique constraint violation
    for i, step in enumerate(remaining_steps):
        step.order = i + len(remaining_steps) + 1
        session.add(step)

    await session.flush()  # Flush to separate the temporary order update from the actual order

    # Update the order of the remaining steps based on the new order
    for i, step in enumerate(remaining_steps):
        step.order = i
        session.add(step)

    await session.commit()
    return


async def reorder_test_plan_steps(
    *, session: AsyncSession, db_plan: SessionTestPlan, step_ids: list[uuid.UUID]
):
    """
    Reorder the steps of a test plan based on the provided step ids.

    The order of the steps is determined by the order of the step ids in the list.

    The step ids must be unique and match the existing steps of the test plan.

    :raises RequestValidationError: If the step ids contain duplicates or do not match the existing step ids
    """
    if len(step_ids) != len(set(step_ids)):
        logger.error(f"Step ids contain duplicates: {step_ids}")
        raise RequestValidationError(
            [
                {
                    "loc": ["body", "step_ids"],
                    "msg": "Step ids contain duplicates",
                    "type": "value_error",
                }
            ]
        )

    existing_step_ids = [step.id for step in db_plan.steps]

    if set(step_ids) != set(existing_step_ids):
        logger.error(
            f"Tried to reorder steps using {step_ids} but existing steps are {existing_step_ids}"
        )
        raise RequestValidationError(
            [
                {
                    "loc": ["body", "step_ids"],
                    "msg": "Step ids mismatch",
                    "type": "value_error",
                }
            ]
        )

    # Assign temporary order to all steps to avoid unique constraint violation
    for db_step in db_plan.steps:
        db_step.order = db_step.order + len(db_plan.steps)
        session.add(db_step)
    await session.flush()  # Flush to separate the temporary order update from the actual order

    # Update the order of the steps based on the new order
    for db_step in db_plan.steps:
        new_order = step_ids.index(db_step.id)
        db_step.order = new_order
        session.add(db_step)
    await session.commit()

    return


async def read_test_plan_step(
    *, session: AsyncSession, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> Optional[SessionTestPlanStep]:
    statement = (
        select(SessionTestPlanStep)
        .where(SessionTestPlanStep.id == step_id)
        .where(SessionTestPlanStep.test_plan_id == test_plan_id)
    )

    res = await session.execute(statement)
    return res.scalar_one_or_none()


def _validate_test_cases(test_cases: list[str]):
    """
    Uses the core PlanStep.validate_same_test_target method to validate the test cases format and same target.

    :param test_cases: List of test cases to be validated
    :raises ValidationError: If the test cases are not from the same test target
    """
    try:
        core_plan.PlanStep.validate_same_test_target(
            [core_plan.StepTestCase(xctest_id=test_case) for test_case in test_cases]
        )
    except ValueError as e:
        raise RequestValidationError(
            [
                {
                    "loc": ["body", "test_cases"],
                    "msg": "Invalid test case path",
                    "type": "value_error",
                }
            ]
        ) from e
