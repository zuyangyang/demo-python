from fastapi import APIRouter, Query

from app.schemas.hello import HelloResponse


router = APIRouter()


@router.get("/hello", response_model=HelloResponse)
def read_hello(name: str | None = Query(default=None, description="Optional name to personalize the greeting")) -> HelloResponse:
    message = "Hello, World" if not name else f"Hello, {name}"
    return HelloResponse(message=message)


