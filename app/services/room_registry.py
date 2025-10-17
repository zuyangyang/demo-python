from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, List, Tuple


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
    # Event sequencing
    next_seq: int = 1
    event_log: List[Tuple[int, bytes]] = field(default_factory=list)
    # Snapshots as (seq, doc_bytes)
    snapshots: List[Tuple[int, bytes]] = field(default_factory=list)
    # Versions tag -> seq
    versions: Dict[str, int] = field(default_factory=dict)


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

    # CRDT/event operations (opaque bytes updates)
    async def append_update(self, room_id: str, update_bytes: bytes) -> int:
        state = await self.get_or_throw(room_id)
        async with state.lock:
            seq = state.next_seq
            state.next_seq += 1
            state.event_log.append((seq, update_bytes))
            return seq

    async def get_updates_after(self, room_id: str, last_seq: int) -> list[tuple[int, bytes]]:
        state = await self.get_or_throw(room_id)
        # No lock for read-only snapshot of list; results are immutable tuples
        return [entry for entry in state.event_log if entry[0] > last_seq]

    async def take_snapshot(self, room_id: str) -> tuple[int, bytes]:
        state = await self.get_or_throw(room_id)
        async with state.lock:
            # Materialize doc by applying events after last snapshot
            base_seq = state.snapshots[-1][0] if state.snapshots else 0
            # For this in-memory demo, the doc is a simple concatenation of bytes
            doc = bytearray()
            if state.snapshots:
                doc.extend(state.snapshots[-1][1])
            for seq, payload in state.event_log:
                if seq > base_seq:
                    doc.extend(payload)
            snapshot_bytes = bytes(doc)
            head_seq = state.next_seq - 1 if state.next_seq > 1 else 0
            state.snapshots.append((head_seq, snapshot_bytes))
            return head_seq, snapshot_bytes

    async def prune_events_before_oldest_snapshot(self, room_id: str) -> int:
        state = await self.get_or_throw(room_id)
        async with state.lock:
            if not state.snapshots:
                return 0
            oldest_seq = state.snapshots[0][0]
            before_len = len(state.event_log)
            state.event_log = [e for e in state.event_log if e[0] > oldest_seq]
            return before_len - len(state.event_log)

    async def tag_version(self, room_id: str, tag: str, seq: Optional[int] = None) -> int:
        state = await self.get_or_throw(room_id)
        async with state.lock:
            if tag in state.versions:
                raise ValueError("version tag already exists")
            head_seq = state.next_seq - 1 if state.next_seq > 1 else 0
            target = head_seq if seq is None else seq
            state.versions[tag] = target
            return target

    async def revert_to_version(self, room_id: str, tag: str) -> tuple[int, bytes]:
        state = await self.get_or_throw(room_id)
        async with state.lock:
            if tag not in state.versions:
                raise KeyError("version tag not found")
            target_seq = state.versions[tag]
            # Compute snapshot up to target_seq
            doc = bytearray()
            # If there is a snapshot <= target_seq, start from it
            base_seq = 0
            if state.snapshots:
                candidates = [s for s in state.snapshots if s[0] <= target_seq]
                if candidates:
                    base_seq, snap_bytes = candidates[-1]
                    doc.extend(snap_bytes)
            for seq, payload in state.event_log:
                if base_seq < seq <= target_seq:
                    doc.extend(payload)
            # Append a new event marking revert as a no-op update to advance head
            seq = state.next_seq
            state.next_seq += 1
            # Store a synthetic update that encodes the revert target (not used by clients, testing aid)
            marker = f"REVERT:{tag}:{target_seq}".encode()
            state.event_log.append((seq, marker))
            return target_seq, bytes(doc)


# Singleton registry for app lifetime
room_registry = RoomRegistry()


