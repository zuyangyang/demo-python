from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import APIException


# Set up logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="A multi-user task assignment system for design projects",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com", "testserver"]
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log request
    logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time
        }
    )

    return response

# Global exception handler
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions."""
    logger.error(
        "API exception occurred",
        extra={
            "error_message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "url": str(request.url)
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(
        "HTTP exception occurred",
        extra={
            "error_message": exc.detail,
            "status_code": exc.status_code,
            "url": str(request.url)
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "details": {}
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        "Unexpected error occurred",
        extra={
            "error_message": str(exc),
            "type": type(exc).__name__,
            "url": str(request.url)
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "details": {}
            }
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "System is running",
        "version": settings.version,
        "debug": settings.debug
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Multi-User Task Assignment System API",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health"
    }

# Include API routers
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


