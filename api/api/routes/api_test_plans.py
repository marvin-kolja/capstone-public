from fastapi import APIRouter

router = APIRouter(prefix="/test-plans", tags=["testPlans"])


@router.get("/")
async def list_test_plans():
    """
    List user created test plans.
    """
    pass


@router.post("/")
async def create_test_plan():
    """
    Create a new test plan.
    """
    pass


@router.get("/{test_plan_id}")
async def read_test_plan(test_plan_id: str):
    """
    Get a test plan.
    """
    pass


@router.patch("/{test_plan_id}")
async def update_test_plan(test_plan_id: str):
    """
    Update a test plan.
    """
    pass


@router.delete("/{test_plan_id}")
async def delete_test_plan(test_plan_id: str):
    """
    Delete a test plan.
    """
    pass
