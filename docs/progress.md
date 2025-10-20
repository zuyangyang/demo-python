## Phase 1: Scaffold Service

Purpose: Establish a runnable FastAPI app with in-memory scaffolding.

Tasks:
- [ ] Scaffold FastAPI app entry and router wiring
- [ ] Add Pydantic v2 base schemas package
- [ ] Add make targets for run, test, lint
- [ ] Document local run in README

Unit Tests:
- [ ] test_main.py::test_docs_available – ensure /docs serves OpenAPI UI

Integration Tests:
- [ ] test_health.py::test_root_status – GET / returns 200 JSON

✅ Done: 

## Phase 2: Document CRUD

Purpose: Provide RESTful CRUD for Document per PRD.

Tasks:
- [ ] Implement POST/GET/PATCH/DELETE /v1/documents endpoints
- [ ] Define DocumentCreate/Update/Response schemas
- [ ] Add in-memory repository for documents
- [ ] Support pagination (page,size) with bounds

Unit Tests:
- [ ] test_documents_repo.py::test_create_and_get – repo stores and retrieves
- [ ] test_documents_schema.py::test_validation – validates title required

Integration Tests:
- [ ] test_documents_api.py::test_create_document – 201 + payload
- [ ] test_documents_api.py::test_list_pagination – page/size respected

✅ Done: 

## Phase 3: CRDT Core (Ops & State)

Purpose: Implement minimal text CRDT and operation application.

Tasks:
- [ ] Implement site_id + site_counter op_id generation
- [ ] Implement insert/delete operations with deterministic ordering
- [ ] Materialize current text and cache invalidation
- [ ] Idempotent apply using op_id set

Unit Tests:
- [ ] test_crdt.py::test_interleaved_inserts_converge – same final text
- [ ] test_crdt.py::test_idempotent_apply – duplicate op ignored

Integration Tests:
- [ ] test_state_api.py::test_get_state_after_ops – GET /v1/documents/{id}/state matches expected

✅ Done: 

## Phase 4: Realtime WebSocket

Purpose: Broadcast accepted CRDT ops to all connected sessions per document.

Tasks:
- [ ] Add WS endpoint /v1/ws/documents/{id}
- [ ] Maintain per-document connection set and presence
- [ ] Validate ops, apply, then broadcast to peers
- [ ] Tie operations to submitted_by when session has user_id

Unit Tests:
- [ ] test_ws.py::test_broadcast_format – message schema validated

Integration Tests:
- [ ] test_ws_integration.py::test_two_clients_receive_ops – both clients receive and apply

✅ Done: 

## Phase 5: Versioning & Revert

Purpose: Snapshot versions and revert document to a prior version.

Tasks:
- [ ] Implement POST /v1/documents/{id}/versions to snapshot
- [ ] Implement GET list/GET single version endpoints
- [ ] Implement POST /v1/versions/{version_id}/revert to create new head
- [ ] Store snapshot_text for O(1) revert and reset CRDT state

Unit Tests:
- [ ] test_versions.py::test_snapshot_creates_version – version log increments
- [ ] test_versions.py::test_revert_restores_text – snapshot restored exactly

Integration Tests:
- [ ] test_versions_api.py::test_revert_endpoint – revert returns new head version

✅ Done: 

## Phase 6: Attribution & Filters

Purpose: Record authorship and expose optional filters.

Tasks:
- [ ] Record created_by/updated_by on documents
- [ ] Record created_by on versions and submitted_by on operations
- [ ] Add optional query filters ?created_by=, ?updated_by=

Unit Tests:
- [ ] test_attribution.py::test_document_updated_by – updates set correctly

Integration Tests:
- [ ] test_documents_api.py::test_filter_by_creator – list filtered

✅ Done: 

## Phase 7: Quality Bar

Purpose: Meet acceptance criteria on docs, coverage, and stability.

Tasks:
- [ ] Ensure OpenAPI schema completeness and tags
- [ ] Achieve ≥ 80% coverage with pytest + cov
- [ ] Add basic error handling and consistent responses

Unit Tests:
- [ ] test_errors.py::test_validation_error_shape – error schema validated

Integration Tests:
- [ ] test_end_to_end.py::test_two_clients_converge – end-to-end CRDT convergence

✅ Done: 
