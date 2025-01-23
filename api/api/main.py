from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, APIRouter, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.utils import is_body_allowed_for_status_code
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from api.config import settings
from api.custom_responses import HTTPExceptionResponse
from api.depends import async_job_runner
from api.log_config import LOGGING_CONFIG
from api.routes import devices, api_test_plans, projects, api_test_session


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


api_router = APIRouter()
api_router.include_router(devices.router)
api_router.include_router(projects.router)
api_router.include_router(api_test_plans.router)
api_router.include_router(api_test_session.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async_job_runner.start_scheduler()
        yield
    finally:
        async_job_runner.shutdown_scheduler()


app = FastAPI(
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
    servers=[
        {
            "url": "http://127.0.0.1",
            # The server is only accessible locally. The port is excluded on purpose as it is not known at this point.
            # As we are running this server only on localhost, the application should find a free port to bind to.
            # Clients that use the OpenAPI specification will have to provide the port themselves.
            "description": "The local running server",
        },
        {
            "url": "http://127.0.0.1:8000",
            "description": "The development server",
        },
    ],
    root_path="/",
    root_path_in_servers=False,
)


@app.exception_handler(500)
async def internal_exception_handler(request: Request, exc: Exception):
    return HTTPExceptionResponse(500, "Internal server error")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return HTTPExceptionResponse(422, exc.errors())


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    headers = getattr(exc, "headers", None)
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=headers)
    return HTTPExceptionResponse(exc.status_code, exc.detail)


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        # TODO: Find and use free port in production. We could also do this from outside and pass it as a parameter.
        reload=settings.ENVIRONMENT == "local",
        log_config=LOGGING_CONFIG,
    )
