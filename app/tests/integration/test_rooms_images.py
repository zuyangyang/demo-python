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

    # upload a small valid PNG generated via bytes; ensure Pillow can open it
    # Use a real 1x1 PNG
    minimal_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )
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


