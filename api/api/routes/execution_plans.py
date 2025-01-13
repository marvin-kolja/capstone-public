from fastapi import APIRouter

router = APIRouter(prefix="/execution-plans", tags=["executionPlans"])


@router.get("/")
async def list_execution_plans():
    """
    List all execution plans.
    """
    pass


@router.post("/")
async def create_execution_plan():
    """
    Create a new execution plan.
    """
    pass


@router.get("/{execution_plan_id}")
async def read_execution_plan(execution_plan_id: int):
    """
    Get the details of an execution plan.
    """
    pass
