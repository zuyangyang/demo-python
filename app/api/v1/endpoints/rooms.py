from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path

from app.schemas.room import RoomCreateRequest, RoomResponse
from app.services.room_registry import room_registry


router = APIRouter(prefix="/rooms")


@router.post("", response_model=RoomResponse)
async def create_room(payload: RoomCreateRequest) -> RoomResponse:
    try:
        state = await room_registry.create_room(payload.room_id)
    except ValueError:
        raise HTTPException(status_code=409, detail={"message": "room already exists"})
    return RoomResponse(room_id=state.room_id, has_image=state.base_image_bytes is not None)


@router.get("", response_model=list[RoomResponse])
async def list_rooms() -> list[RoomResponse]:
    states = await room_registry.list_rooms()
    return [RoomResponse(room_id=s.room_id, has_image=s.base_image_bytes is not None) for s in states]


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str = Path(min_length=1)) -> RoomResponse:
    state = await room_registry.get_room(room_id)
    if state is None:
        raise HTTPException(status_code=404, detail={"message": "room not found"})
    return RoomResponse(room_id=state.room_id, has_image=state.base_image_bytes is not None)


@router.delete("/{room_id}")
async def delete_room(room_id: str = Path(min_length=1)) -> dict[str, bool]:
    ok = await room_registry.delete_room(room_id)
    if not ok:
        raise HTTPException(status_code=404, detail={"message": "room not found"})
    return {"ok": True}


