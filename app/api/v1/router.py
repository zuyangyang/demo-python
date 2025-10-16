from fastapi import APIRouter

from app.api.v1.endpoints.hello import router as hello_router
from app.api.v1.endpoints.health import router as health_router


api_v1_router = APIRouter()
api_v1_router.include_router(hello_router, tags=["hello"])
api_v1_router.include_router(health_router, tags=["health"])


