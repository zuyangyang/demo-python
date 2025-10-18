from fastapi import APIRouter

from app.api.v1.endpoints.hello import router as hello_router
from app.api.v1.endpoints.rooms import router as rooms_router
from app.api.v1.endpoints.images import router as images_router
from app.api.v1.endpoints.ws import router as ws_router
from app.api.v1.endpoints.annotations import router as annotations_router
from app.api.v1.endpoints.comments import router as comments_router


api_v1_router = APIRouter()
api_v1_router.include_router(hello_router, tags=["hello"])
api_v1_router.include_router(rooms_router, tags=["rooms"])
api_v1_router.include_router(images_router, tags=["images"])
api_v1_router.include_router(ws_router, tags=["ws"])
api_v1_router.include_router(annotations_router, tags=["annotations"])
api_v1_router.include_router(comments_router, tags=["comments"])


