from fastapi import APIRouter

from app.api.v1.endpoints.hello import router as hello_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.websocket import router as websocket_router


api_v1_router = APIRouter()
api_v1_router.include_router(hello_router, tags=["hello"])
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_v1_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])


