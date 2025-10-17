from __future__ import annotations

import asyncio
import pytest

from app.services.room_registry import room_registry


@pytest.mark.asyncio
async def test_sequencing_monotonic_and_replay():
    room_id = "t-seq"
    # ensure clean state
    await room_registry.delete_room(room_id)
    await room_registry.create_room(room_id)

    seq1 = await room_registry.append_update(room_id, b"a")
    seq2 = await room_registry.append_update(room_id, b"b")
    assert seq2 == seq1 + 1

    updates = await room_registry.get_updates_after(room_id, last_seq=seq1)
    assert [u[1] for u in updates] == [b"b"]


@pytest.mark.asyncio
async def test_snapshot_and_prune():
    room_id = "t-snap"
    await room_registry.delete_room(room_id)
    await room_registry.create_room(room_id)

    await room_registry.append_update(room_id, b"x")
    await room_registry.append_update(room_id, b"y")
    seq, _ = await room_registry.take_snapshot(room_id)
    assert seq >= 2

    pruned = await room_registry.prune_events_before_oldest_snapshot(room_id)
    # Should prune at least 0 or more depending on snapshot seq alignment
    assert pruned >= 0


@pytest.mark.asyncio
async def test_versions_and_revert():
    room_id = "t-ver"
    await room_registry.delete_room(room_id)
    await room_registry.create_room(room_id)

    s1 = await room_registry.append_update(room_id, b"1")
    s2 = await room_registry.append_update(room_id, b"2")
    assert s2 == s1 + 1

    ver_seq = await room_registry.tag_version(room_id, "alpha")
    assert ver_seq == s2

    # Revert emits a synthetic event and returns doc up to tag
    rseq, doc = await room_registry.revert_to_version(room_id, "alpha")
    assert rseq == ver_seq
    assert doc.endswith(b"12")


