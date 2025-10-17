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


def test_ws_malformed_presence_handling():
    # create room
    resp = client.post("/api/v1/rooms", json={"room_id": "room-malformed"})
    assert resp.status_code == 200

    with client.websocket_connect("/api/v1/ws/rooms/room-malformed?userId=u1") as ws:
        # send malformed presence (missing type)
        ws.send_json({"cursor": {"x": 1, "y": 2}})
        error_msg = ws.receive_json()
        assert error_msg["type"] == "error"
        assert "Invalid presence data format" in error_msg["message"]
        
        # send malformed presence (invalid cursor type)
        ws.send_json({"type": "presence", "cursor": "invalid"})
        error_msg = ws.receive_json()
        assert error_msg["type"] == "error"
        assert "Invalid presence data format" in error_msg["message"]


def test_ws_reconnect_with_presence_restoration():
    # create room
    resp = client.post("/api/v1/rooms", json={"room_id": "room-reconnect"})
    assert resp.status_code == 200

    # First connection - establish presence
    with client.websocket_connect("/api/v1/ws/rooms/room-reconnect?userId=u1") as ws1:
        ws1.send_json({"type": "presence", "cursor": {"x": 10, "y": 20}})
        # Wait a bit to ensure presence is stored
        import time
        time.sleep(0.1)
    
    # Second connection - should receive existing presence
    with client.websocket_connect("/api/v1/ws/rooms/room-reconnect?userId=u2") as ws2:
        # Should receive u1's presence
        msg = ws2.receive_json()
        assert msg["type"] == "presence"
        assert msg["userId"] == "u1"
        assert msg["cursor"] == {"x": 10, "y": 20}


