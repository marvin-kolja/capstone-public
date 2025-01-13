from fastapi import APIRouter

router = APIRouter(prefix="/test-session", tags=["testSession"])


@router.get("/")
async def list_test_sessions():
    """
    List all test sessions.
    """
    pass


@router.post("/")
async def create_test_session():
    """
    Create a new test session.
    """
    pass


@router.get("/{test_session_id}")
async def read_test_session(test_session_id: str):
    """
    Get the details of a test session.
    """
    pass


@router.post("/{test_session_id}/start")
async def start_test_session(test_session_id: str):
    """
    Starts running a test session.
    """
    pass


@router.post("/{test_session_id}/cancel")
async def cancel_test_session(test_session_id: str):
    """
    Cancels a running test session.
    """
    pass


@router.get("/{test_session_id}/update-stream")
async def stream_test_session_updates(test_session_id: str):
    """
    Stream test session updates.
    """
    pass


@router.get("/{test_session_id}/results")
async def list_test_session_results(test_session_id: str):
    """
    Get the results of a test session.
    """
    pass


@router.post("/{test_session_id}/results/export")
async def export_test_session_results(test_session_id: str):
    """
    Start exporting the results of a test session.
    """
    pass
