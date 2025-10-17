import asyncio
import pytest

from app.services.room_registry import RoomRegistry


@pytest.mark.asyncio
async def test_create_and_get_room():
    reg = RoomRegistry()
    state = await reg.create_room("r1")
    assert state.room_id == "r1"
    got = await reg.get_room("r1")
    assert got is state


@pytest.mark.asyncio
async def test_duplicate_room_rejected():
    reg = RoomRegistry()
    await reg.create_room("r1")
    with pytest.raises(ValueError):
        await reg.create_room("r1")


@pytest.mark.asyncio
async def test_delete_room():
    reg = RoomRegistry()
    await reg.create_room("r1")
    ok = await reg.delete_room("r1")
    assert ok is True
    ok2 = await reg.delete_room("r1")
    assert ok2 is False


@pytest.mark.asyncio
async def test_set_and_get_image():
    reg = RoomRegistry()
    await reg.create_room("r1")
    await reg.set_room_image("r1", b"abc")
    img = await reg.get_room_image("r1")
    assert img == b"abc"


