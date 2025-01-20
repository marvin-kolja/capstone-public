from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.routing import APIRoute

from api.config import settings
from api.depends import async_job_runner
from api.routes import devices, api_test_plans, projects, api_test_session


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


api_router = APIRouter()
api_router.include_router(devices.router)
api_router.include_router(api_test_plans.router)
api_router.include_router(projects.router)
api_router.include_router(api_test_session.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async_job_runner.start_scheduler()
        yield
    finally:
        async_job_runner.shutdown_scheduler()


app = FastAPI(generate_unique_id_function=custom_generate_unique_id, lifespan=lifespan)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.ENVIRONMENT == "local",
    )
