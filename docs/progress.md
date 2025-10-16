### TDD Implementation Progress

This document is the authoritative step plan. Each step lists: deliverables, tests, and how to run.

- [x] Author PRD (`docs/prd.md`)
- [x] Create TDD progress tracker (`docs/progress.md`)

---

- [x] Step 1: Project setup (SQLite config, healthcheck)
  - Deliverables:
    - `app/core/database.py` with SQLite engine and session ✅
    - `app/core/config.py` exposing `DATABASE_URL` (default sqlite:///./dev.db) ✅
    - Health endpoint `GET /api/v1/health` returning `{status: "ok"}` ✅
  - Tests:
    - Unit: database session can connect and execute `SELECT 1` ✅
    - Integration: `GET /api/v1/health` returns 200 and body `{status: "ok"}` ✅
  - Run:
    - `uv run pytest -k "health or database"` ✅ (11 tests passed)
  - Notes:
    - Used SQLAlchemy 2.0 with proper `text()` wrapper for raw SQL
    - Implemented `check_connection()` function for database health checks
    - Added comprehensive unit and integration tests
    - Health endpoint verified manually: returns `{"status":"ok"}`

- [x] Step 2: Models and Schemas
  - Deliverables:
    - SQLAlchemy models: `documents`, `document_snapshots`, `document_updates` ✅
    - Pydantic v2 schemas: `DocumentCreate`, `DocumentUpdate`, `DocumentOut` ✅
    - Table creation on app startup for dev ✅
  - Tests:
    - Unit: model metadata creates tables in an in-memory SQLite; constraints present ✅
    - Unit: schema validation (title length ≤ 256, non-empty) ✅
  - Run:
    - `pytest -k models` ✅ (22 tests passed)
  - Notes:
    - Created comprehensive SQLAlchemy models with proper foreign key relationships
    - Implemented Pydantic v2 schemas with validation for title length and whitespace
    - Added table creation on app startup via `create_tables()` function
    - All models include proper timestamps via `TimestampMixin`
    - Verified table creation works correctly in SQLite database

- [x] Step 3: Document CRUD (REST)
  - Deliverables:
    - Endpoints in `app/api/v1/endpoints/documents.py` (POST/GET/PATCH/DELETE/GET list) ✅
    - Service layer methods with proper timestamps and soft-delete ✅
  - Tests:
    - Integration: create -> get -> list contains -> patch title -> delete -> list excludes unless `include_deleted` ✅
    - Edge: invalid title returns 400; unknown id returns 404 ✅
  - Run:
    - `pytest -k "documents and not websocket"` ✅ (35 tests passed)
  - Notes:
    - Created comprehensive repository and service layers following the project structure
    - Implemented all REST endpoints with proper error handling and validation
    - Added comprehensive integration tests covering all CRUD operations and edge cases
    - Fixed test isolation issues with database clearing between tests
    - Updated datetime usage to avoid deprecation warnings
    - All endpoints properly integrated into the API router

- [ ] Step 4: WebSocket scaffold (join/state/presence)
  - Deliverables:
    - `GET /ws/documents/{id}` WS endpoint
    - In-memory room registry per document; presence broadcast on join/leave
    - On join: server responds with `state` using latest snapshot (or empty if none)
  - Tests:
    - Integration (WS): two clients connect; both receive `state`; presence events seen by peer
    - Disconnect cleans up presence (peer receives leave or presence removal)
  - Run:
    - `pytest -k websocket`

- [ ] Step 5: Update handling and sequencing
  - Deliverables:
    - Accept `update` with `{opId, baseVersion, actorId, deltaB64}`
    - Dedupe by opId; assign next `seq` atomically; persist update
    - Respond `ack {opId, seq}`; broadcast `remote_update {seq, deltaB64, actorId}`
  - Tests:
    - Integration (WS): client A sends update -> receives ack; client B receives remote_update
    - Unit: repository ensures monotonic `seq` and unique `opId`
  - Run:
    - `pytest -k update`

- [ ] Step 6: Snapshot persistence
  - Deliverables:
    - Repository methods to write and read snapshots
    - Policy: after N updates (config), accept `snapshotB64` message to persist
    - Join path uses snapshot + subsequent updates
  - Tests:
    - Unit: write snapshot at version V, then get updates after V returns only newer
    - Integration: simulate updates, send snapshot, reconnect -> `state.version` >= snapshot version
  - Run:
    - `pytest -k snapshot`

- [ ] Step 7: Presence lifecycle
  - Deliverables:
    - `presence` messages update in-memory cursors; broadcast to peers
    - Idle timeout removes presence
  - Tests:
    - Integration: presence update from A received by B; after disconnect, B no longer receives updates from A
  - Run:
    - `pytest -k presence`

- [ ] Step 8: Tests hardening
  - Deliverables:
    - Unit tests for repositories/services (CRUD, updates, snapshots)
    - Integration tests covering REST + WS happy paths and common errors
  - Tests:
    - `pytest -q` passes; minimal coverage threshold (e.g., 70%)
  - Run:
    - `pytest --maxfail=1 -q`

- [ ] Step 9: DX polish
  - Deliverables:
    - README quickstart, `uvicorn` command, env sample
    - Optional: simple demo script to echo WS updates
  - Tests:
    - Smoke: run server locally; manual WS echo via `websocat` or test script returns `state`
  - Run:
    - `uvicorn app.main:app --reload`

Notes
- Use SQLite (file) for local dev; keep write transactions short
- Clients must use the same CRDT wire format; server treats deltas as opaque



