from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Set


@dataclass
class Presence:
    user_id: str
    cursor: Optional[dict] = None
    selection: Optional[list[str]] = None
    # last updated timestamp for TTL behavior
    updated_ts: float = field(default_factory=lambda: time.time())


@dataclass
class RoomState:
    room_id: str
    base_image_bytes: Optional[bytes] = None
    presence_by_user: Dict[str, Presence] = field(default_factory=dict)
    # Track active websocket connections per room for simple broadcast
    connections: Set["WebSocketLike"] = field(default_factory=set)
    # Serialize updates within a room when needed
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    # TTL for presence cleanup (seconds)
    presence_ttl: float = 30.0


class WebSocketLike:
    """Protocol-like minimal interface for typing. Avoids importing FastAPI types here.

    Any object with an `send_json` coroutine method fits our broadcast needs.
    """

    async def send_json(self, data: dict) -> None:  # pragma: no cover - structural typing only
        raise NotImplementedError


class RoomRegistry:
    """In-memory registry mapping room ids to states."""

    def __init__(self) -> None:
        self._rooms: Dict[str, RoomState] = {}
        self._registry_lock = asyncio.Lock()

    async def create_room(self, room_id: str) -> RoomState:
        async with self._registry_lock:
            if room_id in self._rooms:
                raise ValueError("room already exists")
            state = RoomState(room_id=room_id)
            self._rooms[room_id] = state
            return state

    async def get_room(self, room_id: str) -> Optional[RoomState]:
        # Read access doesn't require the global lock
        return self._rooms.get(room_id)

    async def list_rooms(self) -> list[RoomState]:
        return list(self._rooms.values())

    async def delete_room(self, room_id: str) -> bool:
        async with self._registry_lock:
            return self._rooms.pop(room_id, None) is not None

    # Image operations
    async def set_room_image(self, room_id: str, data: bytes) -> None:
        state = await self.get_or_throw(room_id)
        async with state.lock:
            state.base_image_bytes = data

    async def get_room_image(self, room_id: str) -> Optional[bytes]:
        state = await self.get_or_throw(room_id)
        return state.base_image_bytes

    async def get_or_throw(self, room_id: str) -> RoomState:
        state = await self.get_room(room_id)
        if state is None:
            raise KeyError("room not found")
        return state

    # Presence management
    async def update_presence(self, room_id: str, user_id: str, presence_data: dict) -> None:
        state = await self.get_or_throw(room_id)
        async with state.lock:
            state.presence_by_user[user_id] = Presence(
                user_id=user_id,
                cursor=presence_data.get("cursor"),
                selection=presence_data.get("selection"),
                updated_ts=time.time()
            )

    async def remove_presence(self, room_id: str, user_id: str) -> None:
        state = await self.get_room(room_id)
        if state:
            async with state.lock:
                state.presence_by_user.pop(user_id, None)

    async def cleanup_expired_presence(self, room_id: str) -> None:
        state = await self.get_room(room_id)
        if not state:
            return
        
        current_time = time.time()
        async with state.lock:
            expired_users = [
                user_id for user_id, presence in state.presence_by_user.items()
                if current_time - presence.updated_ts > state.presence_ttl
            ]
            for user_id in expired_users:
                state.presence_by_user.pop(user_id, None)


# Singleton registry for app lifetime
room_registry = RoomRegistry()


