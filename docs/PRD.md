# Project: Collaborative Doc Service (Local CRDT Backend)

## 1. Elevator Pitch (1 line)
Deliver a local FastAPI backend enabling real-time collaborative text editing with CRDT conflict resolution, in-memory storage, and versioning/revert.

## 2. Core Entities
- Document: id:str, title:str, created_at:datetime, updated_at:datetime, created_by:str, updated_by:str|None, site_counter:int, head_version_id:str|None  
- Operation: op_id:str, doc_id:str, site_id:str, submitted_by:str|None, kind:str ("insert"|"delete"), ref:str, payload:str, timestamp:datetime  
- Version: version_id:str, doc_id:str, parent_id:str|None, created_at:datetime, created_by:str, snapshot_text:str, metadata:str|None  
- Session: session_id:str, doc_id:str, user_id:str, connected_at:datetime  

## 3. API Surface (RESTful, no auth unless asked)
POST   /v1/documents                 → create  
GET    /v1/documents                 → list (pagination: page=1, size=20)  
GET    /v1/documents/{id}            → get single  
PATCH  /v1/documents/{id}            → update (title only)  
DELETE /v1/documents/{id}            → delete  

POST   /v1/documents/{id}/versions   → create version snapshot (from current head)  
GET    /v1/documents/{id}/versions   → list versions (pagination: page=1, size=20)  
GET    /v1/versions/{version_id}     → get single version  
POST   /v1/versions/{version_id}/revert → revert document to version (create new head)  

GET    /v1/documents/{id}/state      → get current materialized text  

WEBSOCKET /v1/ws/documents/{id}      → bidirectional CRDT ops stream (broadcast to peers)

## 4. Business Rules
1. Implement a text CRDT (RGA/Logoot-like) that deterministically merges concurrent inserts/deletes using position identifiers and causal order (op_id = site_id + site_counter).  
2. Accept operations over WebSocket; validate and apply idempotently; broadcast accepted ops to all connected sessions for the same document.  
3. Store documents, operations, versions, and sessions in memory (process-local) with thread-safe data structures; avoid external databases.  
4. Materialize document text from CRDT structure on demand; cache the last materialization and invalidate on new operations.  
5. Append a new Version entry on explicit snapshot requests and on revert; store the full snapshot_text for O(1) revert.  
6. Create a new head version on revert and reset the CRDT state to the target snapshot while preserving previous history.  
7. Guarantee eventual consistency: ensure all clients that process the same set of operations reach identical text state.  
8. Enforce pagination for listing endpoints with page>=1 and 1<=size<=100; default page=1, size=20.  
9. Distinguish identity: treat site_id as the client/device identifier used by the CRDT; treat user_id as the logical human identity. Map a session's user_id to operations via submitted_by when known; always include site_id on operations.  

## 5. Acceptance Criteria
- [ ] Return JSON with Pydantic v2 schemas for all endpoints  
- [ ] Expose automatic OpenAPI docs at /docs  
- [ ] Broadcast accepted CRDT operations to all connected sessions for a document via WebSocket  
- [ ] Produce identical final text for two simulated clients after interleaved operations  
- [ ] Restore text on revert to an earlier version and create a new head version  
- [ ] Use in-memory storage only; reset state on process restart  
- [ ] Run `make test` with ≥ 80% coverage (unit + integration)  

## 6. Tech & Run
- Stack: FastAPI, Pydantic v2, uvicorn, pytest, httpx (tests)  
- Port: 8000  
- Env vars: none  
- Storage: in-memory Python structures (dicts/lists); avoid external DB  
- Concurrency: use FastAPI/Starlette WebSocket; implement per-document broadcast and basic presence tracking  

```note
Scope this service for local development: single-process, in-memory state, deterministic CRDT merging, and explicit versioning/revert to validate collaboration.
```
