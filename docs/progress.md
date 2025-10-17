## Project Progress & Test Plans

This document tracks the implementation progress phase-by-phase. Each step includes a comprehensive test plan to minimize regressions and bugs. Mark items as `[x]` when completed.

---

### Phase 0 — Project scaffolding and foundations

- [ ] Scaffold FastAPI app with structured layout and config
  - Deliverables: `app/main.py`, `app/api/v1/router.py`, `app/core/{config,exceptions}.py`, `app/tests/*`, `README` updates
  - Test plan
    - Unit
      - Ensure app loads without exceptions (import smoke test).
      - Validate settings defaults and env parsing with Pydantic v2.
      - Error handler returns JSON structure for known exceptions.
    - Integration
      - `GET /healthz` returns 200 `{ "ok": true }`.
      - `GET /metrics` returns 200 and JSON with expected keys.
      - Run uvicorn locally: app starts and serves both endpoints.
    - Tooling
      - Ruff/flake checks pass; pytest runs zero tests without failure.

- [ ] Logging & error handling baselines
  - Deliverables: structured logs (roomId, userId if present), exception middleware
  - Test plan
    - Unit: simulated exception triggers correct HTTP status and body.
    - Integration: 404/422 paths return structured JSON; logs contain correlation ids.

---

### Phase 1 — Rooms, images, and basic WebSocket

- [ ] In-memory `RoomRegistry` and `RoomState`
  - Deliverables: create/get/list/delete rooms; `presence` map; `lock`
  - Test plan
    - Unit: `RoomRegistry` create/delete semantics; duplicate id rejection; lock serialization smoke test.
    - Integration: CRUD endpoints return expected payloads and status codes.

- [ ] Base image upload/retrieval
  - Deliverables: `POST /v1/rooms/{id}/image`, `GET /v1/rooms/{id}/image`
  - Test plan
    - Unit: image validator (MIME and extension), max size enforcement, error messages.
    - Integration: upload PNG/JPG, retrieve bytes; invalid type rejected; oversized image rejected.
    - Edge: overwrite image for a room; retrieving before upload returns 404.

- [ ] WebSocket presence echo
  - Deliverables: `GET /v1/ws/rooms/{id}?userId=...`; broadcast presence/cursor JSON
  - Test plan
    - Integration: two clients connect to same room; presence from A is received by B within 100ms median.
    - Edge: send malformed presence → server responds with error message and keeps connection.
    - Disconnect/reconnect: presence removed after TTL; reconnect restores presence.

---

### Phase 2 — CRDT core, sequencing, snapshots

- [ ] CRDT integration (y-py preferred)
  - Deliverables: per-room `crdt_doc`; binary WS frames for updates
  - Test plan
    - Unit: apply CRDT update produces expected doc state; serialization/deserialization roundtrip stable.
    - Integration: two clients exchange updates and converge to same state.

- [ ] Event sequencing and replay
  - Deliverables: `event_log` with monotonic `seq`; join with `lastSeq` to replay
  - Test plan
    - Unit: concurrent updates under lock always increment `seq` by 1; no gaps.
    - Integration: client disconnects after seq N, others continue; upon reconnect with `lastSeq=N`, client replays deltas and matches head state.
    - Fault: corrupted update is rejected and logged; subsequent valid updates continue.

- [ ] Snapshots and pruning
  - Deliverables: periodic/manual snapshots; keep last K; prune events before oldest snapshot
  - Test plan
    - Unit: snapshot writes capture current doc hash; applying snapshot+tail equals live doc.
    - Integration: heavy stream of updates triggers snapshot; old events pruned; memory usage decreases.
    - Edge: revert to older version then resume editing preserves monotonic `seq` (no reuse).

- [ ] Versions and revert
  - Deliverables: tag → seq mapping; revert endpoint
  - Test plan
    - Unit: creating version stores correct seq; duplicate tag rejected.
    - Integration: revert to tag restores doc state (hash match) and broadcasts new head.

---

### Phase 3 — Annotation primitives and comments

- [ ] Annotation schema and operations
  - Deliverables: types (text, line, rect, ellipse, polygon, freehand) with geometry, transforms, styles, z-order
  - Test plan
    - Unit: schema validation for each type; invalid fields rejected with clear errors.
    - Integration: create/update/delete flows via CRDT; concurrent edits on same object converge.
    - Conflict: style and transform changes from two clients merge without data loss.

- [ ] Comment threads
  - Deliverables: threads with `anchor: annotationId | coordinate`, `status: open|resolved`
  - Test plan
    - Unit: create/resolve/reopen state machine; invalid transitions rejected.
    - Integration: comments visible across clients; resolved threads hidden if filtered.

- [ ] Read APIs (optional materialized view)
  - Deliverables: REST read endpoints to fetch current annotations/comments snapshot
  - Test plan
    - Integration: REST read equals CRDT-derived state; after updates, read reflects latest within bounded delay.

---

### Phase 4 — Export pipeline (in-process)

- [ ] Export queue and endpoints
  - Deliverables: enqueue job, status polling, download
  - Test plan
    - Unit: parameter validation (format, scale, background, includeComments); invalid params rejected.
    - Integration: enqueue → completes → status=done; download returns correct MIME and size.

- [ ] Deterministic rendering
  - Deliverables: renderer composes base image + annotations + optional comment overlays
  - Test plan
    - Golden: fixed state renders to expected PNG hash; JPG within SSIM/PSNR threshold.
    - Edge: large canvas and many objects render under time budget; text rendering stable across runs.

---

### Phase 5 — Performance, robustness, polish

- [ ] Batching/throttling and backpressure
  - Deliverables: coalesce frequent updates (≤16ms ticks); handle slow consumers
  - Test plan
    - Perf: simulate freehand stream (1000+ updates/min); verify broadcast latency p50 < 50ms, p95 < 150ms.
    - Robustness: slow consumer gets dropped gracefully; others unaffected.

- [ ] Observability enhancements
  - Deliverables: `/metrics` counters; structured logs with trace ids
  - Test plan
    - Integration: metrics reflect live connections, ops/sec, export queue depth; logs include roomId and seq for key events.

- [ ] Retention/pruning & failure handling
  - Deliverables: K-snapshot retention, event pruning, worker retries, in-memory dead-letter
  - Test plan
    - Integration: long-run test (30–60 min) with continuous edits; memory plateau due to pruning.
    - Failure: inject renderer error → job moved to dead-letter; status exposes error.

---

### Sign-off checklist (per phase)

- Docs updated (`PRD`, `README`, this `progress.md`).
- Tests green (unit + integration); added goldens where applicable.
- Manual acceptance tested (two browser tabs) for realtime behavior and exports.


