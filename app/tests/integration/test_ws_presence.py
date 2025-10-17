from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ws_presence_echo_between_two_clients():
    # create room
    resp = client.post("/api/v1/rooms", json={"room_id": "room-ws"})
    assert resp.status_code == 200

    with client.websocket_connect("/api/v1/ws/rooms/room-ws?userId=u1") as ws1, \
         client.websocket_connect("/api/v1/ws/rooms/room-ws?userId=u2") as ws2:
        # send from ws1
        ws1.send_json({"type": "presence", "cursor": {"x": 1, "y": 2}})
        msg = ws2.receive_json()
        assert msg["type"] == "presence"
        assert msg["cursor"] == {"x": 1, "y": 2}
        assert msg["userId"] == "u1"


