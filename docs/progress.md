# Progress Tracker – Multi-Elevator Scheduling System

Reference: `prd-elevator-system.md`

---

## Phase 1: Project Scaffolding & Core Models

Purpose: Set up FastAPI structure and define all Pydantic schemas and enums.

Tasks:
- [ ] Create enums in `app/core/enums.py` (ElevatorState, DoorState, Direction, RequestStatus)
- [ ] Create Pydantic schemas in `app/schemas/elevator.py` (Elevator, ElevatorCreate, ElevatorResponse)
- [ ] Create Pydantic schemas in `app/schemas/building.py` (BuildingConfig, BuildingConfigUpdate)
- [ ] Create Pydantic schemas in `app/schemas/request.py` (ExternalRequest, InternalRequest, HeartbeatPayload)
- [ ] Create in-memory storage service in `app/services/storage_service.py` (singleton pattern)
- [ ] Initialize storage with default BuildingConfig (total_floors=10, heartbeat_timeout=30)

Unit Tests:
- [ ] test_enums.py::test_elevator_state_values – assert all enum values defined
- [ ] test_enums.py::test_door_state_values – assert all enum values defined
- [ ] test_schemas.py::test_elevator_schema_validation – validate required fields
- [ ] test_schemas.py::test_heartbeat_payload_validation – validate datetime parsing
- [ ] test_storage_service.py::test_singleton_pattern – assert same instance returned

Integration Tests:
- [ ] N/A for this phase

✅ Done: 

---

## Phase 2: Elevator Management APIs

Purpose: Implement CRUD operations for elevator registration and management.

Tasks:
- [ ] Create `app/services/elevator_service.py` with register, delete, get, list methods
- [ ] Create `app/api/v1/endpoints/elevators.py` with POST /v1/elevators endpoint
- [ ] Add DELETE /v1/elevators/{elevator_id} endpoint
- [ ] Add GET /v1/elevators endpoint with pagination (page, size)
- [ ] Add GET /v1/elevators/{elevator_id} endpoint
- [ ] Register elevator router in `app/api/v1/router.py`
- [ ] Validate initial_floor is within building floor range

Unit Tests:
- [ ] test_elevator_service.py::test_register_elevator – assert elevator created with WAITING state
- [ ] test_elevator_service.py::test_delete_elevator – assert elevator removed from storage
- [ ] test_elevator_service.py::test_get_nonexistent_elevator – assert raises 404
- [ ] test_elevator_service.py::test_list_elevators_pagination – assert page/size limits work

Integration Tests:
- [ ] test_elevators.py::test_register_elevator_success – POST returns 201 with elevator data
- [ ] test_elevators.py::test_delete_elevator_success – DELETE returns 204
- [ ] test_elevators.py::test_get_elevator_not_found – GET returns 404
- [ ] test_elevators.py::test_list_elevators_empty – GET returns empty list

✅ Done: 

---

## Phase 3: Building Configuration APIs

Purpose: Implement APIs to configure total floors and retrieve building settings.

Tasks:
- [ ] Create `app/services/building_service.py` with update_floors, get_config methods
- [ ] Create `app/api/v1/endpoints/building.py` with PUT /v1/building/floors endpoint
- [ ] Add GET /v1/building/config endpoint
- [ ] Add validation: total_floors must be >= 1
- [ ] Register building router in `app/api/v1/router.py`

Unit Tests:
- [ ] test_building_service.py::test_update_total_floors – assert config updated
- [ ] test_building_service.py::test_update_floors_invalid – assert raises error for floors < 1
- [ ] test_building_service.py::test_get_config – assert returns current BuildingConfig

Integration Tests:
- [ ] test_building.py::test_update_floors_success – PUT returns 200 with updated config
- [ ] test_building.py::test_update_floors_invalid – PUT returns 422 for invalid value
- [ ] test_building.py::test_get_config_default – GET returns default config

✅ Done: 

---

## Phase 4: Scheduling Algorithm & External Requests

Purpose: Implement intelligent elevator dispatching for external up/down button requests.

Tasks:
- [ ] Create `app/services/scheduler_service.py` with calculate_score and assign_elevator methods
- [ ] Implement scoring algorithm as per PRD section 8 (score 1, 2-5, 6-15, 99)
- [ ] Create `app/services/request_service.py` for request management
- [ ] Create `app/api/v1/endpoints/requests.py` with POST /v1/requests/external endpoint
- [ ] Add GET /v1/requests/external endpoint with status filter
- [ ] Validate requested floor is within building floor range
- [ ] Auto-assign elevator when external request created

Unit Tests:
- [ ] test_scheduler_service.py::test_score_waiting_at_floor – assert score = 1
- [ ] test_scheduler_service.py::test_score_moving_same_direction – assert score 2-5
- [ ] test_scheduler_service.py::test_score_waiting_different_floor – assert score 6-15
- [ ] test_scheduler_service.py::test_score_moving_opposite_direction – assert score = 99
- [ ] test_scheduler_service.py::test_exclude_trouble_elevators – assert score = 999
- [ ] test_scheduler_service.py::test_assign_nearest_elevator – assert lowest score wins

Integration Tests:
- [ ] test_requests.py::test_create_external_request_success – POST returns 201 with assigned elevator
- [ ] test_requests.py::test_create_external_request_floor_out_of_range – POST returns 400
- [ ] test_requests.py::test_list_external_requests_filter_status – GET filters by status

✅ Done: 

---

## Phase 5: Internal Requests

Purpose: Handle destination floor selection from inside elevators.

Tasks:
- [ ] Add POST /v1/requests/internal endpoint in `app/api/v1/endpoints/requests.py`
- [ ] Add GET /v1/requests/internal endpoint with elevator_id and status filters
- [ ] Add create_internal_request method in `app/services/request_service.py`
- [ ] Validate destination_floor is within building range
- [ ] Validate elevator_id exists before creating request

Unit Tests:
- [ ] test_request_service.py::test_create_internal_request – assert request created with PENDING status
- [ ] test_request_service.py::test_internal_request_invalid_elevator – assert raises 404
- [ ] test_request_service.py::test_internal_request_invalid_floor – assert raises 400

Integration Tests:
- [ ] test_requests.py::test_create_internal_request_success – POST returns 201
- [ ] test_requests.py::test_create_internal_request_nonexistent_elevator – POST returns 404
- [ ] test_requests.py::test_list_internal_requests_filter_elevator – GET filters by elevator_id

✅ Done: 

---

## Phase 6: Elevator State & Door Operations

Purpose: Implement state transition and door operation APIs with business rule validation.

Tasks:
- [ ] Create `app/services/state_service.py` with validate_state_transition, validate_door_operation methods
- [ ] Add PATCH /v1/elevators/{id}/state endpoint in `app/api/v1/endpoints/elevators.py`
- [ ] Add PATCH /v1/elevators/{id}/door endpoint
- [ ] Enforce rule: door operations only in WAITING or TROUBLE state
- [ ] Enforce rule: cannot transition to UP/DOWN unless door is CLOSED
- [ ] Auto-close doors when transitioning to UP/DOWN state

Unit Tests:
- [ ] test_state_service.py::test_door_operation_in_waiting_allowed – assert door state changes
- [ ] test_state_service.py::test_door_operation_in_up_rejected – assert raises 400 error
- [ ] test_state_service.py::test_transition_to_up_with_open_door_rejected – assert raises 400
- [ ] test_state_service.py::test_transition_to_up_auto_closes_door – assert door becomes CLOSED
- [ ] test_state_service.py::test_valid_state_transitions – assert WAITING to UP/DOWN allowed

Integration Tests:
- [ ] test_elevators.py::test_change_door_state_success – PATCH returns 200
- [ ] test_elevators.py::test_change_door_while_moving_rejected – PATCH returns 400
- [ ] test_elevators.py::test_change_state_with_open_door_rejected – PATCH returns 400
- [ ] test_elevators.py::test_change_state_success – PATCH returns 200 with updated state

✅ Done: 

---

## Phase 7: Heartbeat & Health Monitoring

Purpose: Implement heartbeat endpoint and background task to detect stale elevators.

Tasks:
- [ ] Add POST /v1/elevators/{id}/heartbeat endpoint in `app/api/v1/endpoints/elevators.py`
- [ ] Update elevator state, floor, telemetry, and last_heartbeat timestamp on heartbeat
- [ ] Add GET /v1/elevators/health endpoint returning count by state
- [ ] Create `app/services/monitor_service.py` with check_heartbeat_timeouts method
- [ ] Create background task in `app/main.py` that runs monitor every 10 seconds
- [ ] Mark elevator as TROUBLE if no heartbeat within heartbeat_timeout_seconds

Unit Tests:
- [ ] test_monitor_service.py::test_detect_stale_elevator – assert marked as TROUBLE
- [ ] test_monitor_service.py::test_healthy_elevator_not_marked – assert stays in current state
- [ ] test_elevator_service.py::test_process_heartbeat – assert updates all fields

Integration Tests:
- [ ] test_elevators.py::test_heartbeat_success – POST returns 200 with updated elevator
- [ ] test_elevators.py::test_heartbeat_updates_timestamp – assert last_heartbeat changes
- [ ] test_elevators.py::test_heartbeat_nonexistent_elevator – POST returns 404
- [ ] test_elevators.py::test_health_summary – GET returns count by state
- [ ] test_monitor.py::test_background_task_marks_stale_elevator – assert TROUBLE after timeout

✅ Done: 

---

## Phase 8: Integration Tests & Documentation

Purpose: End-to-end flow validation, error handling, and final documentation.

Tasks:
- [ ] Write integration test for full flow: register → external request → assign → heartbeat → complete
- [ ] Write integration test for multiple elevators competing for same request
- [ ] Write integration test for elevator deletion cancels internal requests
- [ ] Add custom exception handlers in `app/core/exceptions.py`
- [ ] Add proper error responses with detail messages as per PRD section 8
- [ ] Verify OpenAPI docs at /docs show all endpoints correctly
- [ ] Run `uv run pytest --cov=app --cov-report=term-missing` and ensure ≥ 80% coverage
- [ ] Update README.md with setup instructions, API usage examples, and architecture overview

Unit Tests:
- [ ] N/A for this phase

Integration Tests:
- [ ] test_end_to_end.py::test_full_elevator_lifecycle – register, request, assign, move, complete
- [ ] test_end_to_end.py::test_multiple_elevators_scheduling – assert nearest elevator assigned
- [ ] test_end_to_end.py::test_elevator_deletion_cancels_requests – assert internal requests cancelled
- [ ] test_end_to_end.py::test_heartbeat_timeout_excludes_from_scheduling – assert TROUBLE elevator skipped

✅ Done: 

---

## Summary

- Total Phases: 8
- Estimated Completion: TBD
- Current Phase: Phase 1
- Test Coverage Target: ≥ 80%

