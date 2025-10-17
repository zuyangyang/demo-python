from __future__ import annotations

import asyncio
import pytest
from starlette.websockets import WebSocketDisconnect

from app.main import app
from fastapi.testclient import TestClient
from app.services.room_registry import room_registry


client = TestClient(app)


def _ws_path(room_id: str, user: str, last_seq: int | None = None) -> str:
    base = f"/api/v1/ws/rooms/{room_id}?userId={user}"
    if last_seq is not None:
        base += f"&lastSeq={last_seq}"
    return base


def test_ws_binary_exchange_and_replay():
    room_id = "i-ws"
    # Setup room
    with client as c:
        # Create room via REST
        resp = c.post("/api/v1/rooms", json={"room_id": room_id})
        assert resp.status_code in (200, 201, 409)

        with c.websocket_connect(_ws_path(room_id, "A")) as ws_a:
            with c.websocket_connect(_ws_path(room_id, "B")) as ws_b:
                # Send presence from A
                ws_a.send_json({"type": "presence", "cursor": {"x": 1, "y": 2}})
                # B should receive presence
                msg = ws_b.receive_json()
                assert msg.get("type") == "presence"

                # Send binary update from A
                ws_a.send_bytes(b"upd-1")
                # B should receive binary payload
                payload = ws_b.receive_bytes()
                assert payload == b"upd-1"

        # Now connect C with lastSeq=0 to get replay of all updates
        with c.websocket_connect(_ws_path(room_id, "C", last_seq=0)) as ws_c:
            # Should replay b"upd-1"
            recv = ws_c.receive_bytes()
            assert recv == b"upd-1"


