from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path
from fastapi import Body

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


@router.post("/{room_id}/snapshots")
async def create_snapshot(room_id: str = Path(min_length=1)) -> dict[str, int | bytes]:
    try:
        seq, _ = await room_registry.take_snapshot(room_id)
        # Do not return bytes body in JSON response; return seq only
        return {"seq": seq}
    except KeyError:
        raise HTTPException(status_code=404, detail={"message": "room not found"})


@router.post("/{room_id}/versions/{tag}")
async def create_version(
    room_id: str = Path(min_length=1),
    tag: str = Path(min_length=1),
    payload: dict | None = Body(default=None)
) -> dict[str, int]:
    try:
        target_seq = payload.get("seq") if isinstance(payload, dict) else None
        seq = await room_registry.tag_version(room_id, tag, seq=target_seq)
        return {"seq": seq}
    except KeyError:
        raise HTTPException(status_code=404, detail={"message": "room not found"})
    except ValueError:
        raise HTTPException(status_code=409, detail={"message": "version tag already exists"})


@router.post("/{room_id}/versions/{tag}/revert")
async def revert_version(room_id: str = Path(min_length=1), tag: str = Path(min_length=1)) -> dict[str, int]:
    try:
        seq, _ = await room_registry.revert_to_version(room_id, tag)
        return {"seq": seq}
    except KeyError:
        raise HTTPException(status_code=404, detail={"message": "room or tag not found"})


