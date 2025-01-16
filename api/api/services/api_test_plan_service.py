import logging
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from api.db_models import (
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
) -> SessionTestPlanPublic:
    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)
    return SessionTestPlanPublic.model_validate(db_plan)


def update_test_plan(
    *, session: Session, test_plan_id: uuid.UUID, plan: SessionTestPlanUpdate
) -> SessionTestPlanPublic:
    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)
    update_db_model(db_model=db_plan, new_data_model=plan)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return SessionTestPlanPublic.model_validate(db_plan)


def delete_test_plan(*, session: Session, test_plan_id: uuid.UUID):
    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)
    session.delete(db_plan)
    session.commit()
    return


def create_test_plan_step(
    *, session: Session, test_plan_id: uuid.UUID, step: SessionTestPlanStepCreate
) -> SessionTestPlanStepPublic:
    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)
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
    test_plan_id: uuid.UUID,
    step_id: uuid.UUID,
    step: SessionTestPlanStepUpdate,
) -> SessionTestPlanStepPublic:
    db_step = _get_test_plan_step_or_raise(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )
    update_db_model(db_model=db_step, new_data_model=step)
    session.add(db_step)
    session.commit()
    session.refresh(db_step)
    return SessionTestPlanStepPublic.model_validate(db_step)


def delete_test_plan_step(
    *, session: Session, test_plan_id: uuid.UUID, step_id: uuid.UUID
):
    db_step = _get_test_plan_step_or_raise(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )
    session.delete(db_step)
    session.commit()
    return


def reorder_test_plan_steps(
    *, session: Session, test_plan_id: uuid.UUID, step_ids: list[uuid.UUID]
):
    if len(step_ids) != len(set(step_ids)):
        logger.error(f"Step ids contain duplicates: {step_ids}")
        raise HTTPException(status_code=400, detail="Step ids contain duplicates")

    db_plan = _get_test_plan_or_raise(session=session, test_plan_id=test_plan_id)

    existing_step_ids = [step.id for step in db_plan.steps]

    if set(step_ids) != set(existing_step_ids):
        logger.error(
            f"Tried to reorder steps using {step_ids} but existing steps are {existing_step_ids}"
        )
        raise HTTPException(status_code=400, detail="Step ids mismatch")

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


def _get_test_plan_or_raise(
    *, session: Session, test_plan_id: uuid.UUID
) -> SessionTestPlan:
    plan = session.exec(
        select(SessionTestPlan).where(SessionTestPlan.id == test_plan_id)
    ).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Test plan not found")
    return plan


def _get_test_plan_step(
    *, session: Session, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> Optional[SessionTestPlanStep]:
    return session.exec(
        select(SessionTestPlanStep)
        .where(SessionTestPlanStep.id == step_id)
        .where(SessionTestPlanStep.test_plan_id == test_plan_id)
    ).first()


def _get_test_plan_step_or_raise(
    *, session: Session, test_plan_id: uuid.UUID, step_id: uuid.UUID
) -> SessionTestPlanStep:
    step = _get_test_plan_step(
        session=session, test_plan_id=test_plan_id, step_id=step_id
    )
    if step is None:
        raise HTTPException(status_code=404, detail="Step not found")
    return step
