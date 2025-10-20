## Phase 1: Scaffold Service & In-Memory Store

Purpose: Set up FastAPI app skeleton, in-memory repositories, and base schemas.

Tasks:
- [ ] Scaffold FastAPI app entry and router wiring
- [ ] Create in-memory repositories for Document, Annotation, Version, ExportJob
- [ ] Define Pydantic v2 base schemas and ID/timestamp utilities
- [ ] Implement pagination helpers (page, size)

Unit Tests:
- [ ] app/tests/unit/test_utils.py::test_generate_uuid – asserts UUIDv4 format
- [ ] app/tests/unit/test_pagination.py::test_paginate_basic – asserts page/size slicing

Integration Tests:
- [ ] app/tests/integration/test_health.py::test_openapi_available – GET /docs returns 200

✅ Done:

## Phase 2: Documents CRUD

Purpose: Provide RESTful CRUD for documents with timestamps and version field.

Tasks:
- [ ] Implement POST/GET(list)/GET(id)/PATCH/DELETE for /v1/documents
- [ ] Enforce ISO8601 timestamps and soft-delete
- [ ] Increment document.version on updates

Unit Tests:
- [ ] app/tests/unit/test_documents_repo.py::test_create_read_document – repo create/read works

Integration Tests:
- [ ] app/tests/integration/test_documents.py::test_create_document – 201 + payload schema
- [ ] app/tests/integration/test_documents.py::test_list_documents_pagination – 200 + paged results

✅ Done:

## Phase 3: Annotations CRUD + Optimistic Versioning

Purpose: CRUD for annotations bound to document_id with version conflict handling.

Tasks:
- [ ] Implement /v1/annotations CRUD with document_id filter
- [ ] Maintain Annotation.version and 409 on stale updates
- [ ] Soft-delete via status=deleted

Unit Tests:
- [ ] app/tests/unit/test_annotations_repo.py::test_conflict_on_stale_version – raises conflict

Integration Tests:
- [ ] app/tests/integration/test_annotations.py::test_create_annotation – 201 + schema
- [ ] app/tests/integration/test_annotations.py::test_update_conflict – 409 on stale version

✅ Done:

## Phase 4: Versioning Snapshots & Revert

Purpose: Snapshot current document+annotations and support revert to prior version.

Tasks:
- [ ] Implement POST /v1/versions (snapshot)
- [ ] Implement GET /v1/versions and GET /v1/versions/{id}
- [ ] Implement POST /v1/versions/{id}/revert

Unit Tests:
- [ ] app/tests/unit/test_versions_repo.py::test_snapshot_structure – includes annotations state

Integration Tests:
- [ ] app/tests/integration/test_versions.py::test_revert_restores_state – 200 and state restored

✅ Done:

## Phase 5: Realtime WebSocket Broadcasts

Purpose: Broadcast annotation CRUD and presence events by document_id room.

Tasks:
- [ ] Implement WS /v1/realtime?document_id=<id>
- [ ] Broadcast create/update/delete and version events to connected clients
- [ ] Add basic join/leave presence messages

Unit Tests:
- [ ] app/tests/unit/test_ws_room.py::test_room_broadcast – all peers receive message

Integration Tests:
- [ ] app/tests/integration/test_realtime.py::test_ws_broadcast_annotation – both clients receive event

✅ Done:

## Phase 6: Export Jobs (PNG/JPG) to Local Files

Purpose: Render base image + annotations server-side and save to ./exports/.

Tasks:
- [ ] Implement POST /v1/exports (enqueue), GET list, GET status, GET download
- [ ] Compose with Pillow and write ./exports/{job_id}.{ext}
- [ ] Serve exports/ statically and expose result_url

Unit Tests:
- [ ] app/tests/unit/test_renderer.py::test_draw_box_text_arrow – draws without error

Integration Tests:
- [ ] app/tests/integration/test_exports.py::test_export_png_and_download – 200 and file exists

✅ Done:

## Phase 7: QA, Coverage, Docs

Purpose: Achieve ≥ 80% coverage, finalize OpenAPI and README.

Tasks:
- [ ] Add missing tests to reach ≥ 80% coverage
- [ ] Verify /docs and schemas for all endpoints
- [ ] Update README.md with run/test instructions

Unit Tests:
- [ ] app/tests/unit/test_coverage_marker.py::test_import_all_modules – ensures importability

Integration Tests:
- [ ] app/tests/integration/test_smoke.py::test_smoke_all_endpoints – 2xx across endpoints

✅ Done:


