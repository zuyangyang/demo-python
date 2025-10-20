# Project: Real-Time Collaborative Image Annotation Service

## 1. Elevator Pitch (1 line)
Deliver a Canva-like real-time annotation backend that manages annotations, replies, versions, and export jobs using an in-memory store.

## 2. Core Entities
- Annotation: id:str, type:str (text|box|arrow|comment), geometry:object, style:object, content:str, parent_id:Optional[str], version:int, created_at:str (ISO8601), updated_at:str (ISO8601), created_by:str, updated_by:str, status:str (active|deleted), document_id:str
- Document: id:str, name:str, image_url:str, created_at:str (ISO8601), updated_at:str (ISO8601), version:int
- Version: id:str, document_id:str, number:int, created_at:str (ISO8601), created_by:str, change_summary:str
- ExportJob: id:str, document_id:str, status:str (queued|processing|completed|failed), format:str (png|jpg), result_url:Optional[str], created_at:str (ISO8601), completed_at:Optional[str]

## 3. API Surface (RESTful, no auth unless asked)
POST   /v1/documents        → create  
GET    /v1/documents        → list (pagination: page=1, size=20)  
GET    /v1/documents/{id}   → get single  
PATCH  /v1/documents/{id}   → update  
DELETE /v1/documents/{id}   → delete  

POST   /v1/annotations        → create  
GET    /v1/annotations        → list (pagination: page=1, size=20, filter by document_id)  
GET    /v1/annotations/{id}   → get single  
PATCH  /v1/annotations/{id}   → update  
DELETE /v1/annotations/{id}   → delete  

POST   /v1/versions                 → create snapshot for document  
GET    /v1/versions                 → list (pagination: page=1, size=20, filter by document_id)  
GET    /v1/versions/{id}            → get single  
POST   /v1/versions/{id}/revert     → revert document to version  

POST   /v1/exports                   → enqueue export job (document_id, format)  
GET    /v1/exports                   → list (pagination: page=1, size=20, filter by document_id)  
GET    /v1/exports/{id}              → get job status  
GET    /v1/exports/{id}/download     → download resulting image file (when completed)  

WebSocket (for real-time updates, optional in MVP HTTP surface):  
WS /v1/realtime?document_id=<id>  → broadcast annotation CRUD and presence events

## 4. Business Rules
1. Store all entities in process memory using Python dictionaries keyed by `id`.  
2. Generate `id` as UUIDv4 strings on creation.  
3. Enforce `document_id` on all `Annotation`, `Version`, and `ExportJob` operations.  
4. Accept and return timestamps as ISO8601 strings; set `created_at` on create and `updated_at` on update.  
5. Increment `Annotation.version` on each update; reject updates when client supplies an older `version` (409).  
6. Treat `DELETE` as soft-delete by setting `status=deleted`; exclude deleted from default list results.  
7. Create `Version` snapshots by capturing current `Document` and all non-deleted `Annotation` states.  
8. Revert to a `Version` by replacing current annotations and document version with the snapshot state and incrementing `Document.version`.  
9. Queue `ExportJob` in memory and process server-side. On start, set `status=processing`; on success set `status=completed`, else `failed`.  
10. Render export by compositing `Document.image_url` as the background and drawing all non-deleted `Annotation`s on top using server-side rendering (Pillow):  
    - Draw `box` as stroked/fill rectangles per `geometry` and `style`.  
    - Draw `arrow` as line with arrowhead using stroke in `style`.  
    - Draw `text` using font, size, color from `style` at `geometry` position.  
    - Treat `comment` as non-visual unless it is a `text` annotation; do not render discussion threads.  
    - Respect z-order by creation time ascending (older first) unless `style` includes explicit `z_index`.  
11. Write the rendered file to local filesystem under `./exports/{job_id}.{ext}` (create `exports/` if missing); set `result_url` to `/exports/{job_id}.{ext}`.  
12. Expose `GET /v1/exports/{id}/download` to stream the local file when `status=completed`; return 404 if not completed.  
10. Paginate list endpoints with `page` and `size` query params; default `page=1`, `size=20`.  
11. Validate request/response bodies with Pydantic v2 models; return 422 on validation errors.  
12. Broadcast annotation create/update/delete and document version events to connected clients for the same `document_id` over WebSocket.

## 5. Acceptance Criteria
- [ ] All endpoints return JSON + Pydantic schema.  
- [ ] Automatic OpenAPI docs reachable at /docs.  
- [ ] `make test` runs ≥ 80 % coverage.  
- [ ] In-memory store supports concurrent requests in a single process.  
- [ ] List endpoints implement pagination with `page` and `size`.  
- [ ] Version creation and revert restore annotations and document version accurately.  
- [ ] WebSocket broadcasts reflect CRUD changes to annotations within the same `document_id`.  
- [ ] Export jobs progress through statuses and expose `result_url` when completed.  
- [ ] Deletes are soft and excluded from default lists.  
- [ ] 409 Conflict is returned on stale `version` updates.

## 6. Tech & Run
- Stack: FastAPI, Pydantic v2, Pillow, Uvicorn, pytest.  
- Storage: In-memory Python dictionaries; no external database; data resets on process restart.  
- Port: 8000.  
- Env vars: none.  
- Start: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.  
- Test: `make test` (provide pytest config and tests).  
- Notes: Single-process execution; avoid multi-worker deployment for MVP to maintain in-memory consistency. Ensure `exports/` directory is writable and served as static files.


