## Product Requirements Document (PRD): Real-time Collaborative Image Annotation (Local, In-Memory)

### 1. Overview

- **Purpose**: Build a local, single-process backend service that enables 2+ users to simultaneously annotate a Canva-style image with real-time synchronization, view presence, comments, versioning, and export to PNG/JPG. The service is designed for local development with in-memory storage only.
- **Scope**: One FastAPI project providing REST and WebSocket APIs. All data (rooms, documents, events, snapshots, exports) is held in memory and lost on restart. Access control is out of scope and delegated to an external service.
- **Primary value**: Low-latency multi-user collaboration with deterministic state via CRDTs, easy local spin-up, and a clean API surface for a frontend prototype.

### 2. Goals and Non-Goals

- **Goals**
  - Real-time multi-user annotation with conflict-free merges using CRDT.
  - In-memory storage for rooms, snapshots, event logs, and export jobs.
  - Room/session abstraction with presence and cursors.
  - Annotation primitives: text boxes, arrows/lines, shapes, freehand; styles; z-order; grouping.
  - Commenting: threads anchored to annotations or coordinates; resolve/reopen.
  - Versioning: append-only event log, periodic snapshots, named versions, revert.
  - Export: render to PNG/JPG at current or specified version; configurable scale and background.
  - Single-process workers: export queue and periodic snapshotter.

- **Non-Goals**
  - Access control, authentication, or authorization (handled elsewhere).
  - Cross-process clustering, HA, or persistent databases.
  - Third-party notifications, email, or webhooks.
  - Unlimited room sizes or internet-scale load; target is local/dev.

### 3. Users and Use Cases

- **Users**: Designers, PMs, engineers collaborating locally on an image with annotations.
- **Use cases**
  - Multiple users add/modify text boxes, arrows, and shapes in real time.
  - Users leave comments pinned to elements or coordinates and resolve threads.
  - A user reverts the canvas to a previous version.
  - A user exports the annotated image as PNG/JPG for sharing.

### 4. Core Concepts

- **Room**: A collaboration space bound to a base image. Holds CRDT document, event log, snapshots, presence, versions.
- **CRDT Document**: Canonical canvas state using Yjs (via y-py) or Automerge; holds layers/shapes/text/comments.
- **Event Log**: Append-only list of CRDT binary updates with monotonically increasing `seq`.
- **Snapshot**: Periodic binary serialization of the CRDT with a `seq` watermark.
- **Version**: User-defined tag/name pointing to a `seq`.
- **Presence**: Ephemeral cursors/selections/typing indicators per user.

### 5. Functional Requirements

- **Realtime collaboration**
  - 2+ concurrent users in the same room via WebSocket.
  - Low-latency broadcast of CRDT updates; server sequences events and relays.
  - Presence updates (cursor position, selection) as ephemeral messages.
  - Reconnect with last known `seq` to replay missed updates.

- **Annotation primitives**
  - Create/update/delete: text, arrow/line, rectangle/ellipse, polygon, freehand path.
  - Transformations: move, resize, rotate; z-order; grouping/ungrouping.
  - Styles: fill/stroke color, width, opacity, font family/size/weight, text alignment.

- **Comments**
  - Threaded comments anchored to an annotation ID or to a coordinate point.
  - States: open, resolved; ability to reopen.

- **Versioning and history**
  - Append-only event log with strictly increasing `seq` per room.
  - Periodic in-memory snapshots (by time or operation count).
  - Named versions (tag → seq); revert room state to a specific version/tag.

- **Export**
  - Export to PNG or JPG from the latest state or any specified `seq`/version tag.
  - Parameters: format (png|jpg), scale/DPI, background (transparent/white), include_comments (bool).
  - Enqueue export job; worker renders and stores result in memory; downloadable via REST.

- **Rooms and images**
  - Create/delete a room; upload a base image; fetch the current base image.
  - List rooms; retrieve room metadata.

- **Observability (dev)**
  - Health endpoint; simple in-memory counters (connected clients, ops/sec, export jobs).

### 6. Non-Functional Requirements

- **Performance**: End-to-end annotation latency target <100ms on localhost; binary updates; batch noisy ops at 8–16ms intervals.
- **Reliability**: Best-effort ordering (per-room lock); reconnection replay; data volatile on process restart.
- **Scalability**: Suitable for 2–10 concurrent users per room on a single process.
- **Security**: No ACL; assume upstream authentication/authorization; TLS not required for local dev.

### 7. System Architecture (Single Process, In-Memory)

- **FastAPI service**
  - REST for rooms, images, versions, exports, comments, snapshots.
  - WebSocket for CRDT updates and presence.
  - Background tasks: export worker and snapshot compactor.

- **In-memory registries**
  - `RoomRegistry`: `room_id → RoomState`.
  - `ExportQueue`: `asyncio.Queue[ExportJob]`.
  - `ExportResults`: `job_id → ExportResult`.

- **RoomState**
  - `room_id: str`
  - `base_image: bytes | PIL.Image.Image`
  - `crdt_doc: YDoc`
  - `event_log: list[Event(seq:int, ts:float, user:str, payload:bytes)]`
  - `snapshots: list[Snapshot(seq:int, ts:float, blob:bytes, checksum:str)]`
  - `versions: dict[str, int]`  // tag → seq
  - `presence: dict[user_id, Awareness]`
  - `lock: asyncio.Lock`  // serialize updates, ensure seq monotonicity

- **Workers**
  - Export worker reconstructs state at `seq` (snapshot + tail) and renders with Pillow/Cairo/Skia-Python; stores bytes in `ExportResults`.
  - Snapshotter periodically writes snapshots per room and prunes old events before the oldest retained snapshot.

### 8. API Design (Representative)

- **Rooms**
  - `POST /v1/rooms` → { id }
  - `GET /v1/rooms` → list
  - `GET /v1/rooms/{roomId}` → metadata
  - `DELETE /v1/rooms/{roomId}`

- **Images**
  - `POST /v1/rooms/{roomId}/image` (multipart or raw bytes)
  - `GET /v1/rooms/{roomId}/image` (stream)

- **Realtime (WebSocket)**
  - `GET /v1/ws/rooms/{roomId}?userId=...&lastSeq=...`
  - Messages (binary for CRDT updates; JSON for control/presence):

```json
{
  "type": "presence",
  "userId": "u1",
  "cursor": { "x": 100, "y": 200 },
  "selection": ["anno-123"]
}
```

- **Snapshots & Versions**
  - `POST /v1/rooms/{roomId}/snapshots` → { seq }
  - `GET /v1/rooms/{roomId}/versions` → [{ tag, seq }]
  - `POST /v1/rooms/{roomId}/versions` (body: { tag, seq? })
  - `POST /v1/rooms/{roomId}/versions/{tag}:revert` → { seq }

- **Comments**
  - `GET /v1/rooms/{roomId}/comments`
  - `POST /v1/rooms/{roomId}/comments`
  - `PATCH /v1/rooms/{roomId}/comments/{commentId}` (resolve/reopen)

- **Exports**
  - `POST /v1/rooms/{roomId}/exports` (body: { format, seq|tag, scale, includeComments, background }) → { jobId }
  - `GET /v1/exports/{jobId}` → { status, mime?, size? }
  - `GET /v1/exports/{jobId}/download` (stream bytes)

- **Health & Metrics**
  - `GET /healthz`
  - `GET /metrics`

### 9. WebSocket Protocol Details

- **Connection**: Client connects with `roomId`, `userId`, optional `lastSeq`.
- **Handshake**: Server sends `roomInfo { seq, snapshotSeq }` and optionally a recent snapshot if client is far behind.
- **CRDT sync**: Binary Yjs (or Automerge) updates; server sequences each as `Event(seq, ts, user)` and broadcasts.
- **Presence**: JSON messages with cursor/selection; not stored in CRDT; TTL’d in `presence` map; periodically rebroadcast.
- **Replay**: If `lastSeq < headSeq`, server replays `event_log` entries [lastSeq+1..headSeq].

### 10. Rendering and Export

- **Input**: Base image + CRDT-derived annotation objects/materialized view at target `seq`.
- **Output**: PNG or JPG byte stream; optional comment badges/overlays.
- **Parameters**: format, scale/DPI, background (transparent/white), include_comments.
- **Determinism**: Renderer must be deterministic given the same CRDT state and parameters.

### 11. Data Retention & Pruning (In-Memory)

- Retain up to `K` snapshots per room (configurable, default 5).
- Snapshot every `N` ops (default 200) or `M` seconds (default 30s), whichever comes first.
- Trim `event_log` entries older than the oldest retained snapshot `seq`.

### 12. Constraints & Limitations

- Volatile state: All data lost on process exit.
- Single-process only: No external broker, no cross-process fanout.
- No ACL: Caller must ensure `room_id` and `user_id` are authorized by an upstream service.

### 13. Observability

- Structured logs with roomId, seq, userId, latency.
- Metrics: connected_clients, rooms_active, ops_broadcast_per_sec, export_jobs_pending, export_time_ms.
- `/metrics` returns a simple JSON snapshot for local inspection.

### 14. Testing Strategy

- Unit tests: CRDT update sequencing, snapshot creation/pruning, export rendering determinism.
- Integration tests: 2 WebSocket clients editing concurrently; reconnect with replay; export at tagged version.
- Golden tests: Known annotation state → expected PNG hash (allow small tolerance if using lossy JPG).

### 15. Acceptance Criteria

- Two browser clients in the same room see each other’s edits within 100ms median on localhost.
- Comments can be created, listed, resolved, and are visible to all clients.
- Creating a named version and reverting restores the canvas to that state.
- Export job can be requested and a PNG/JPG can be downloaded; repeated exports stable.
- Process can be restarted without crashing (state is intentionally lost).

### 16. Milestones

- **M1 – Room & Image Basics (WS echo)**: Rooms CRUD, image upload/get, basic WS presence and echo updates.
- **M2 – CRDT Core & Snapshots**: Yjs integration, event log, snapshots, replay on reconnect.
- **M3 – Annotations & Comments**: Full primitive set, styles, comment threads.
- **M4 – Export Worker**: Export queue, renderer, download endpoints, metrics.
- **M5 – Polish & Perf**: Batching/throttling, pruning, determinism checks, docs.

### 17. Open Questions

- CRDT library choice: y-py (Yjs) vs automerge-py—finalize based on availability/perf on target dev machines.
- Renderer: Pillow vs Cairo vs Skia-Python—select based on text shaping/anti-aliasing needs.
- Comment overlays in exports: always visible vs opt-in; default policy?


