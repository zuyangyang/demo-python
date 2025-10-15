from fastapi import APIRouter

from app.api.v1.endpoints.hello import router as hello_router


api_v1_router = APIRouter()
api_v1_router.include_router(hello_router, tags=["hello"])


