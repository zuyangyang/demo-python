### Product Requirements Document (PRD)

## 1. Overview
This service provides core backend capabilities for a Google Docs–style editor focused on:
- Document CRUD (create/read/update/delete metadata and soft delete)
- Multi-user realtime collaborative editing over WebSocket
- Client-driven CRDT updates with server relay and persistence

Out-of-scope features (delegated to other services): version history, comments, search, and authentication/authorization/security hardening.

## 2. Goals and Non‑Goals
- Goals
  - Provide REST endpoints for document lifecycle and listing
  - Provide a WebSocket endpoint for realtime collaboration
  - Relay CRDT updates among connected clients for the same document
  - Persist CRDT snapshots and updates in SQLite for recovery
  - Broadcast basic presence (cursor/selection) to connected peers
- Non‑Goals
  - Implement full version history UI/UX or restore flows
  - Implement comments/mentions/notifications
  - Implement search indexing
  - Implement production-grade auth and RBAC (handled externally)

## 3. Personas and Use Cases
- Persona: Developer or QA running locally; frontend editor uses CRDT (Yjs/Automerge) and connects to this backend.
- Use Cases
  - Create a new document and open it for editing
  - Multiple users join the same document and edit concurrently
  - Reconnect after a network hiccup and recover the latest document state
  - List existing documents and rename or soft-delete them

## 4. Functional Requirements
- REST API (v1)
  - POST /documents: create document with title
  - GET /documents/{id}: fetch document metadata
  - PATCH /documents/{id}: update title and/or soft-delete flag
  - DELETE /documents/{id}: soft delete
  - GET /documents?query=&include_deleted=&page=&page_size=: list documents (basic pagination)
- WebSocket API
  - Path: /ws/documents/{id}
  - On connect: server sends latest state {type: "state", version, snapshotB64}
  - Client messages:
    - join: {type: "join", userId, displayName}
    - update: {type: "update", opId, baseVersion, actorId, deltaB64}
    - presence: {type: "presence", cursor: {from, to}, color?}
    - ping: {type: "ping", ts}
  - Server messages:
    - state: {type: "state", version, snapshotB64}
    - ack: {type: "ack", opId, seq}
    - remote_update: {type: "remote_update", seq, deltaB64, actorId}
    - presence: {type: "presence", userId, cursor}
    - error: {type: "error", code, message}
- CRDT Strategy
  - Clients run CRDT; server relays opaque updates (deltaB64) and persists them
  - Idempotency via opId (unique per client op)
  - baseVersion is advisory for diagnostics; merges handled by client CRDT
- Snapshotting
  - Store periodic snapshots (snapshotB64) and append-only updates with seq
  - Snapshot cadence: every N=200 updates or after T=60s of active edits (configurable)
- Presence
  - Broadcast-only, best effort, not persisted

## 5. Non‑Functional Requirements
- Local development with SQLite file DB (default dev.db)
- Performance (local):
  - Connect and receive state < 300 ms for medium docs (≤ 200 KB snapshot)
  - Broadcast latency p50 < 50 ms, p95 < 150 ms under 10 concurrent editors per doc
- Reliability
  - Durable storage of updates and latest snapshot
  - Sequence monotonicity per document
  - On restart, join flow reconstructs head state by snapshot + updates
- Observability
  - Structured logs with docId/userId/opId/seq where relevant
  - Minimal counters (connections per doc, updates/sec, snapshot events) if added later

## 6. Data Model (SQLite)
- documents
  - id (uuid TEXT PK)
  - title (TEXT, ≤ 256)
  - owner_id (TEXT NULL)
  - created_at (DATETIME)
  - updated_at (DATETIME)
  - deleted_at (DATETIME NULL)
- document_snapshots
  - document_id (TEXT FK -> documents.id)
  - version (INTEGER)
  - snapshot_blob (BLOB)
  - created_at (DATETIME)
  - PK(document_id, version)
- document_updates
  - id (uuid TEXT PK)
  - document_id (TEXT FK)
  - seq (INTEGER)
  - op_id (TEXT UNIQUE)
  - actor_id (TEXT)
  - delta_blob (BLOB)
  - created_at (DATETIME)
  - INDEX(document_id, seq)

## 7. API Specifications (v1)
- POST /api/v1/documents
  - Request: {title: string ≤ 256}
  - Response 201: {id, title, created_at}
- GET /api/v1/documents/{id}
  - Response 200: {id, title, updated_at, deleted_at}
- PATCH /api/v1/documents/{id}
  - Request: {title?: string, deleted?: boolean}
  - Response 200: updated document
- DELETE /api/v1/documents/{id}
  - Response 204
- GET /api/v1/documents?query=&include_deleted=&page=&page_size=
  - Response 200: {items: [...], page, page_size, total}

Errors: 400 validation, 404 not found.

## 8. WebSocket Protocol Details
- Connect: /ws/documents/{id}?userId=...&displayName=...
- Backpressure: per-connection bounded queue; presence may be dropped first
- Keepalive: ping/pong every 30s; disconnect idle clients after configurable timeout (e.g., 2 min)
- Ordering: server assigns per-doc seq to accepted updates; broadcast includes seq

## 9. Persistence & Recovery
- On join: load latest snapshot for document; stream updates with seq > snapshot.version
- Append update transaction:
  - Read MAX(seq) FOR UPDATE equivalent (SQLite serializes writers)
  - Assign seq = max + 1, insert update with op_id uniqueness
  - Return seq; send ack and broadcast
- Snapshot:
  - Accept full CRDT snapshot from a client (preferred) or compute server-side if CRDT lib added later
  - Persist snapshot at current head seq and optionally prune updates with seq ≤ snapshot.version

## 10. Security & Privacy (Minimal for Local Dev)
- No authentication; userId/displayName are client-provided and unauthenticated
- Size limits: max payload for delta/snapshot (configurable; e.g., 1 MB)
- Input validation for REST fields

## 11. Assumptions
- All collaborating clients use the same CRDT format/wire protocol
- Single service instance during local development; SQLite write contention is acceptable
- Network is trusted in local dev; security delegated elsewhere in broader system

## 12. Rollout & Milestones
1) Foundations: project setup, SQLite, config, healthcheck
2) Document CRUD endpoints and schemas
3) WS endpoint with join/state/presence scaffolding
4) Update handling with seq assignment and broadcast
5) Snapshot write/read path and compaction (optional)
6) Basic tests: CRUD and WS happy paths
7) DX: README commands and example clients

## 13. Acceptance Criteria
- CRUD endpoints work with SQLite and pass unit/integration tests
- Two WS clients can join the same doc, exchange updates, and converge
- Server persists updates and snapshot; reconnecting client receives correct state
- Presence messages are seen by peers, and disconnects clean up presence state


