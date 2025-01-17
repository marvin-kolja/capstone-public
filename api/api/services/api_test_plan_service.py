import logging
import uuid
from typing import Optional

from fastapi.exceptions import RequestValidationError
from sqlmodel import Session, select

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


def list_test_plans(*, session: Session) -> list[SessionTestPlanPublic]:
    plans = session.exec(select(SessionTestPlan)).all()
    return [SessionTestPlanPublic.model_validate(plan) for plan in plans]


def create_test_plan(
    *, session: Session, plan: SessionTestPlanCreate
) -> SessionTestPlanPublic:
    db_plan = SessionTestPlan.model_validate(plan)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return SessionTestPlanPublic.model_validate(db_plan)


def read_test_plan(
    *, session: Session, test_plan_id: uuid.UUID
) -> Optional[SessionTestPlan]:
    db_plan = session.exec(
        select(SessionTestPlan).where(SessionTestPlan.id == test_plan_id)
    ).first()
    if db_plan is None:
        return None
    return db_plan


def update_test_plan(
    *, session: Session, db_plan: SessionTestPlan, plan: SessionTestPlanUpdate
) -> SessionTestPlanPublic:
    update_db_model(db_model=db_plan, new_data_model=plan)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return SessionTestPlanPublic.model_validate(db_plan)


def delete_test_plan(*, session: Session, db_plan: SessionTestPlan):
    session.delete(db_plan)
    session.commit()
    return


def create_test_plan_step(
    *, session: Session, db_plan: SessionTestPlan, step: SessionTestPlanStepCreate
) -> SessionTestPlanStepPublic:
    db_step = SessionTestPlanStep.model_validate(
        {
            **step.model_dump(),
            "test_plan_id": db_plan.id,
            "order": len(db_plan.steps),
        }
    )
    db_plan.steps.append(db_step)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return SessionTestPlanStepPublic.model_validate(db_step)


def update_test_plan_step(
    *,
    session: Session,
    db_step: SessionTestPlanStep,
    step: SessionTestPlanStepUpdate,
) -> SessionTestPlanStepPublic:
    update_db_model(db_model=db_step, new_data_model=step)
    session.add(db_step)
    session.commit()
    session.refresh(db_step)
    return SessionTestPlanStepPublic.model_validate(db_step)


def delete_test_plan_step(*, session: Session, db_step: SessionTestPlanStep):
    session.delete(db_step)
    session.commit()
    return


def reorder_test_plan_steps(
    *, session: Session, db_plan: SessionTestPlan, step_ids: list[uuid.UUID]
):
    """
    Reorder the steps of a test plan based on the provided step ids.

    The order of the steps is determined by the order of the step ids in the list.

    The step ids must be unique and match the existing steps of the test plan.

    :raises RequestValidationError: If the step ids contain duplicates or do not match the existing step ids
    """
    if len(step_ids) != len(set(step_ids)):
        logger.error(f"Step ids contain duplicates: {step_ids}")
        raise RequestValidationError("Step ids contain duplicates")

    existing_step_ids = [step.id for step in db_plan.steps]

    if set(step_ids) != set(existing_step_ids):
        logger.error(
            f"Tried to reorder steps using {step_ids} but existing steps are {existing_step_ids}"
        )
        raise RequestValidationError("Step ids mismatch")

    # Assign temporary order to all steps to avoid unique constraint violation
    for db_step in db_plan.steps:
        db_step.order = db_step.order + len(db_plan.steps)
        session.add(db_step)
    session.flush()  # Flush to separate the temporary order update from the actual order

    # Update the order of the steps based on the new order
    for db_step in db_plan.steps:
        new_order = step_ids.index(db_step.id)
        db_step.order = new_order
        session.add(db_step)
    session.commit()

    return


def read_test_plan_step(
    *, session: Session, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> Optional[SessionTestPlanStep]:
    return session.exec(
        select(SessionTestPlanStep)
        .where(SessionTestPlanStep.id == step_id)
        .where(SessionTestPlanStep.test_plan_id == test_plan_id)
    ).first()
