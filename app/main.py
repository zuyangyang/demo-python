from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import create_tables


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(title=settings.app_name, debug=settings.debug)
    application.include_router(api_v1_router, prefix="/api/v1")
    
    # Create database tables on startup
    create_tables()
    
    return application


app = create_app()


