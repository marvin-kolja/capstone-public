import uuid

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from api.custom_responses import SSEStreamingResponse
from api.depends import SessionDep, AsyncJobRunnerDep
from api.models import TestSessionCreate, TestSessionPublic

router = APIRouter(prefix="/test-session", tags=["testSession"])


@router.get("/")
async def list_test_sessions(*, session: SessionDep) -> list[TestSessionPublic]:
    """
    List all test sessions.
    """
    pass


@router.post("/")
async def start_test_session(
    *,
    session: SessionDep,
    job_runner: AsyncJobRunnerDep,
    session_create: TestSessionCreate
) -> TestSessionPublic:
    """
    Create and start new test session.
    """
    pass


@router.get("/{test_session_id}")
async def read_test_session(
    *, session: SessionDep, test_session_id: uuid.UUID
) -> TestSessionPublic:
    """
    Get the details of a test session.
    """
    pass


@router.post("/{test_session_id}/cancel")
async def cancel_test_session(
    *, session: SessionDep, job_runner: AsyncJobRunnerDep, test_session_id: uuid.UUID
):
    """
    Cancels a running test session.
    """
    pass


@router.get("/{test_session_id}/execution-step-stream")
async def stream_execution_step_updates(
    *, session: SessionDep, test_session_id: uuid.UUID
) -> SSEStreamingResponse:
    """
    Stream updates of the execution steps of a test session. Can return any execution step when it is updated.
    """
    pass


@router.post("/{test_session_id}/process-trace-results")
async def export_test_session_results(
    *, session: SessionDep, test_session_id: uuid.UUID
):
    """
    Start processing the trace results of a test session.
    """
    pass
