from fastapi import FastAPI, APIRouter
from fastapi.routing import APIRoute

from api.routes import (
    devices,
    api_test_plans,
    projects,
    execution_plans,
    api_test_session,
)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


api_router = APIRouter()
api_router.include_router(devices.router)
api_router.include_router(api_test_plans.router)
api_router.include_router(projects.router)
api_router.include_router(execution_plans.router)
api_router.include_router(api_test_session.router)


app = FastAPI(generate_unique_id_function=custom_generate_unique_id)
app.include_router(api_router)
