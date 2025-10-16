from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db, check_connection

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Health check endpoint that verifies database connectivity.
    Returns status "ok" if database is accessible, "error" otherwise.
    """
    if check_connection():
        return {"status": "ok"}
    else:
        return {"status": "error"}
