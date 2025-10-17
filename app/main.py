from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import APIException


_process_start_time_sec = time.time()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(title=settings.app_name, debug=settings.debug)

    # Exception handlers
    @application.exception_handler(APIException)
    async def handle_api_exception(request: Request, exc: APIException) -> JSONResponse:  # type: ignore[unused-ignore]
        return JSONResponse(status_code=exc.status_code, content={"error": {"message": exc.message, "status": exc.status_code}})

    # Health & Metrics endpoints (top-level)
    @application.get("/healthz")
    async def healthz() -> dict[str, bool]:
        return {"ok": True}

    @application.get("/metrics")
    async def metrics() -> dict[str, object]:
        uptime_sec = max(0, time.time() - _process_start_time_sec)
        return {
            "ok": True,
            "app_name": settings.app_name,
            "uptime_sec": round(uptime_sec, 3),
        }

    application.include_router(api_v1_router, prefix="/api/v1")
    return application


app = create_app()


