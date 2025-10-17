from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query, WebSocket, WebSocketDisconnect

from app.services.room_registry import RoomState, room_registry


router = APIRouter()


@router.websocket("/ws/rooms/{room_id}")
async def ws_room(
    websocket: WebSocket,
    room_id: str = Path(min_length=1),
    userId: str | None = Query(default=None),
) -> None:
    # accept connection after verifying room exists and userId provided
    state = await room_registry.get_room(room_id)
    if state is None:
        # Cannot send HTTP error after websocket upgrade; reject upfront
        await websocket.close(code=1008)
        return
    if not userId:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await _register_connection(state, websocket)
    try:
        # Simple presence echo protocol: relay any JSON payload to other peers in room
        while True:
            data: Any = await websocket.receive_json()
            # Attach sender userId for consumers
            if isinstance(data, dict):
                data.setdefault("userId", userId)
            await _broadcast(state, websocket, data)
    except WebSocketDisconnect:
        pass
    finally:
        await _unregister_connection(state, websocket)


async def _register_connection(state: RoomState, ws: WebSocket) -> None:
    async with state.lock:
        state.connections.add(ws)  # type: ignore[arg-type]


async def _unregister_connection(state: RoomState, ws: WebSocket) -> None:
    async with state.lock:
        if ws in state.connections:
            state.connections.remove(ws)


async def _broadcast(state: RoomState, sender: WebSocket, data: Any) -> None:
    # Snapshot to avoid iterating while mutating
    targets = [ws for ws in state.connections if ws is not sender]
    for ws in targets:
        try:
            await ws.send_json(data)
        except Exception:
            # Best effort: ignore errors when sending
            continue


