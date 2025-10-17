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
    
    # Send current presence state to new connection
    await _send_current_presence(state, websocket)
    
    try:
        # Enhanced presence echo protocol with error handling
        while True:
            try:
                data: Any = await websocket.receive_json()
                
                # Validate presence data structure
                if not _is_valid_presence_data(data):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid presence data format"
                    })
                    continue
                
                # Update presence in registry
                if isinstance(data, dict) and data.get("type") == "presence":
                    await room_registry.update_presence(room_id, userId, data)
                
                # Attach sender userId for consumers
                if isinstance(data, dict):
                    data.setdefault("userId", userId)
                    
                await _broadcast(state, websocket, data)
                
            except ValueError as e:
                # Malformed JSON
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Invalid JSON: {str(e)}"
                })
                continue
                
    except WebSocketDisconnect:
        pass
    finally:
        await _unregister_connection(state, websocket, userId)


async def _register_connection(state: RoomState, ws: WebSocket) -> None:
    async with state.lock:
        state.connections.add(ws)  # type: ignore[arg-type]


async def _unregister_connection(state: RoomState, ws: WebSocket, user_id: str | None = None) -> None:
    async with state.lock:
        if ws in state.connections:
            state.connections.remove(ws)
    # Intentionally do NOT remove presence here.
    # Presence is retained until TTL expiry and cleaned up by maintenance.


async def _broadcast(state: RoomState, sender: WebSocket, data: Any) -> None:
    # Snapshot to avoid iterating while mutating
    targets = [ws for ws in state.connections if ws is not sender]
    for ws in targets:
        try:
            await ws.send_json(data)
        except Exception:
            # Best effort: ignore errors when sending
            continue


def _is_valid_presence_data(data: Any) -> bool:
    """Validate presence data structure."""
    if not isinstance(data, dict):
        return False
    
    # Must have a type field
    if "type" not in data:
        return False
    
    # If it's a presence message, validate structure
    if data.get("type") == "presence":
        # cursor and selection are optional but if present should be valid
        if "cursor" in data and not isinstance(data["cursor"], dict):
            return False
        if "selection" in data and not isinstance(data["selection"], list):
            return False
    
    return True


async def _send_current_presence(state: RoomState, ws: WebSocket) -> None:
    """Send current presence state to new connection."""
    async with state.lock:
        for user_id, presence in state.presence_by_user.items():
            presence_data = {
                "type": "presence",
                "userId": user_id,
                "cursor": presence.cursor,
                "selection": presence.selection
            }
            try:
                await ws.send_json(presence_data)
            except Exception:
                # Best effort: ignore errors when sending
                continue


