from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import APIException
from app.main import create_app


def _mount_raising_route(application: FastAPI) -> None:
    async def boom() -> dict[str, str]:
        raise APIException("bad things", status_code=418)

    application.add_api_route("/boom", boom, methods=["GET"])  # type: ignore[arg-type]


def test_api_exception_handler_returns_json() -> None:
    app = create_app()
    _mount_raising_route(app)
    client = TestClient(app)

    resp = client.get("/boom")
    assert resp.status_code == 418
    body = resp.json()
    assert body == {"error": {"message": "bad things", "status": 418}}


