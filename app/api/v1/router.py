from fastapi import APIRouter

# Create API router
api_v1_router = APIRouter()

# Include endpoint routers
from app.api.v1.endpoints import hello
api_v1_router.include_router(hello.router, tags=["hello"])

# Include endpoint routers (will be added in later phases)
# from app.api.v1.endpoints import auth, users, tasks, projects
# api_v1_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# api_v1_router.include_router(users.router, prefix="/users", tags=["users"])
# api_v1_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
# api_v1_router.include_router(projects.router, prefix="/projects", tags=["projects"])


