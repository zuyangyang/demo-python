import io

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_rooms_crud_and_image_upload_and_get():
    # list empty
    resp = client.get("/api/v1/rooms")
    assert resp.status_code == 200
    assert resp.json() == []

    # create room
    resp = client.post("/api/v1/rooms", json={"room_id": "r1"})
    assert resp.status_code == 200
    assert resp.json()["room_id"] == "r1"
    assert resp.json()["has_image"] is False

    # get room
    resp = client.get("/api/v1/rooms/r1")
    assert resp.status_code == 200

    # upload invalid empty file
    resp = client.post("/api/v1/rooms/r1/image", files={"file": ("empty.png", b"")})
    assert resp.status_code == 400

    # upload a tiny valid PNG header (minimal)
    # PNG header + IHDR chunk stub (not a full image but imghdr recognizes from header)
    minimal_png = b"\x89PNG\r\n\x1a\n" + b"rest"
    resp = client.post("/api/v1/rooms/r1/image", files={"file": ("img.png", minimal_png, "image/png")})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # get image
    resp = client.get("/api/v1/rooms/r1/image")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")

    # delete room
    resp = client.delete("/api/v1/rooms/r1")
    assert resp.status_code == 200


