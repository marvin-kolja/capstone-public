import logging

from core.tunnel.client import get_tunnel_client
from fastapi import APIRouter
from sqlmodel import text, select

from api.depends import SessionDep
from api.models import HealthCheck, ServerStatus, ResourceStatus

router = APIRouter(tags=["health"])

logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check(db: SessionDep) -> HealthCheck:
    """
    Health check endpoint.

    1. Checks if the DB connection is available.
    2. Checks if the tunnel connect socket server is available.
    """
    db_status: ResourceStatus = "unavailable"
    tunnel_connect_status: ResourceStatus = "unavailable"

    try:
        db.exec(select(text("1"))).first()
        db_status = "ok"
    except Exception:
        logger.error("DB is unavailable", exc_info=True)

    try:
        with get_tunnel_client(port=49151) as client:
            await client.get_tunnel(
                "not-a-real-device-id"
            )  # Dummy request to check if the server is available
            tunnel_connect_status = "ok"
    except Exception:
        logger.error("Tunnel connect socket server is unavailable", exc_info=True)

    status: ServerStatus = (
        "ok" if db_status == "ok" and tunnel_connect_status == "ok" else "unhealthy"
    )

    return HealthCheck(
        status=status,
        db=db_status,
        tunnel_connect=tunnel_connect_status,
    )
