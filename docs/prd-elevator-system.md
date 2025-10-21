# Project: Multi-Elevator Scheduling System

## 1. Elevator Pitch (1 line)
Intelligent multi-elevator dispatch system that routes elevators to floor requests using optimal scheduling while monitoring elevator health and enforcing safety rules.

## 2. Core Entities

- **Elevator**: id:str, current_floor:int, state:ElevatorState, door_state:DoorState, speed:float, temperature:float, last_heartbeat:datetime, created_at:datetime
- **BuildingConfig**: total_floors:int, heartbeat_timeout_seconds:int (default 30)
- **ExternalRequest**: id:str, floor:int, direction:Direction, requested_at:datetime, assigned_elevator_id:str|null, status:RequestStatus
- **InternalRequest**: id:str, elevator_id:str, destination_floor:int, requested_at:datetime, status:RequestStatus
- **HeartbeatPayload**: elevator_id:str, current_floor:int, speed:float, temperature:float, state:ElevatorState, door_state:DoorState, timestamp:datetime

## 3. Enums

- **ElevatorState**: WAITING, UP, DOWN, TROUBLE
- **DoorState**: OPENED, OPENING, CLOSING, CLOSED
- **Direction**: UP, DOWN
- **RequestStatus**: PENDING, ASSIGNED, COMPLETED, CANCELLED

## 4. API Surface (RESTful, no auth)

```
# Elevator Management
POST   /v1/elevators                    → register new elevator (body: {id:str, initial_floor:int})
DELETE /v1/elevators/{elevator_id}      → delete elevator
GET    /v1/elevators                    → list all elevators (pagination: page=1, size=20)
GET    /v1/elevators/{elevator_id}      → get single elevator details

# Building Configuration
PUT    /v1/building/floors              → set total floors (body: {total_floors:int})
GET    /v1/building/config              → get building configuration

# Floor Requests
POST   /v1/requests/external            → external up/down button (body: {floor:int, direction:Direction})
POST   /v1/requests/internal            → internal destination button (body: {elevator_id:str, destination_floor:int})
GET    /v1/requests/external            → list external requests (filter: status, page, size)
GET    /v1/requests/internal            → list internal requests (filter: elevator_id, status, page, size)

# Elevator Operations
PATCH  /v1/elevators/{elevator_id}/state     → change running state (body: {state:ElevatorState})
PATCH  /v1/elevators/{elevator_id}/door      → change door state (body: {door_state:DoorState})
POST   /v1/elevators/{elevator_id}/heartbeat → receive heartbeat (body: HeartbeatPayload)

# Health & Status
GET    /v1/elevators/health             → get health summary (count by state)
```

## 5. Business Rules

### Elevator State Management
1. New elevators register in WAITING state with door_state CLOSED at specified initial_floor.
2. State transitions allowed: WAITING ↔ UP, WAITING ↔ DOWN, any → TROUBLE.
3. Mark elevator as TROUBLE if no heartbeat received within heartbeat_timeout_seconds (default 30).
4. Elevators in TROUBLE state are excluded from scheduling algorithm.

### Door State Management
5. Door operations (OPENING, CLOSING, OPENED, CLOSED) allowed ONLY when elevator state is WAITING or TROUBLE.
6. Attempting to change door state when elevator state is UP or DOWN returns HTTP 400 with error message.
7. Elevator state cannot transition from WAITING to UP/DOWN unless door_state is CLOSED.
8. Door state must automatically set to CLOSED when elevator transitions to UP or DOWN state.

### Scheduling Algorithm (External Requests)
9. When external request arrives, calculate score for each available elevator:
   - **Score 1**: WAITING at requested floor
   - **Score 2-5**: Moving in same direction as request and will pass requested floor (2 + distance_in_floors)
   - **Score 6-15**: WAITING on different floor (6 + abs(current_floor - requested_floor))
   - **Score 99**: Moving in opposite direction or state is UP/DOWN going away
   - **Exclude**: Elevators in TROUBLE state
10. Assign request to elevator with lowest score.
11. If no available elevator (all in TROUBLE), mark request as PENDING and retry when elevator becomes available.

### Request Handling
12. External request status: PENDING → ASSIGNED (when elevator dispatched) → COMPLETED (when elevator arrives and doors open).
13. Internal request status: PENDING → COMPLETED (when elevator reaches destination floor).
14. Validate requested floor and destination floor are within 1 to total_floors range.
15. Cancel internal requests for an elevator when elevator is deleted.

### Heartbeat Processing
16. Update elevator current_floor, state, door_state, speed, temperature, and last_heartbeat timestamp on each heartbeat.
17. Heartbeat endpoint is idempotent and always returns HTTP 200 with updated elevator state.
18. Run background task every 10 seconds to check heartbeat timeouts and mark stale elevators as TROUBLE.

## 6. Acceptance Criteria

- [ ] All endpoints return JSON with Pydantic schema validation
- [ ] Automatic OpenAPI docs reachable at /docs
- [ ] Scheduling algorithm executes in O(n) time where n = number of elevators
- [ ] Background heartbeat monitor runs continuously and marks stale elevators
- [ ] `uv run pytest` runs with ≥ 80% test coverage
- [ ] Integration tests cover:
  - Register elevator → external request → assign → complete flow
  - Door state validation (reject operations in UP/DOWN state)
  - State transition validation (reject UP/DOWN with open doors)
  - Heartbeat timeout triggers TROUBLE state
  - Multiple elevators compete for same request (nearest wins)
- [ ] Unit tests cover scheduling algorithm with various elevator positions and states
- [ ] API returns proper HTTP status codes:
  - 200 OK for successful GET/PATCH/POST
  - 201 Created for POST elevator
  - 204 No Content for DELETE
  - 400 Bad Request for validation errors
  - 404 Not Found for non-existent elevator_id
  - 422 Unprocessable Entity for invalid state transitions

## 7. Tech & Run

- **Stack**: FastAPI 0.119.0, Pydantic v2, SQLite (in-memory for MVP), pytest, uvicorn[standard]
- **Port**: 8000
- **Env vars**: none (use in-memory SQLite database)
- **Run dev**: `uv run uvicorn app.main:app --reload --port 8000`
- **Run tests**: `uv run pytest -v --cov=app --cov-report=term-missing`
- **Access docs**: http://localhost:8000/docs

## 8. Implementation Notes

### Data Storage (MVP)
- Use in-memory dictionaries for MVP:
  - `elevators: dict[str, Elevator]`
  - `external_requests: dict[str, ExternalRequest]`
  - `internal_requests: dict[str, InternalRequest]`
  - `building_config: BuildingConfig` (singleton)
- Can migrate to SQLite with SQLAlchemy later for persistence.

### Background Tasks
- Implement heartbeat monitor as FastAPI background task using `asyncio.create_task`.
- Monitor runs in infinite loop with 10-second sleep intervals.
- Check `datetime.now() - last_heartbeat > heartbeat_timeout_seconds` for each elevator.

### Scheduling Algorithm Implementation
```python
def calculate_elevator_score(
    elevator: Elevator,
    requested_floor: int,
    requested_direction: Direction
) -> int:
    if elevator.state == ElevatorState.TROUBLE:
        return 999  # Exclude
    
    if elevator.state == ElevatorState.WAITING:
        if elevator.current_floor == requested_floor:
            return 1
        else:
            return 6 + abs(elevator.current_floor - requested_floor)
    
    # Elevator is moving (UP or DOWN)
    if elevator.state.name == requested_direction.name:
        # Same direction
        if (requested_direction == Direction.UP and 
            elevator.current_floor <= requested_floor):
            return 2 + (requested_floor - elevator.current_floor)
        elif (requested_direction == Direction.DOWN and 
              elevator.current_floor >= requested_floor):
            return 2 + (elevator.current_floor - requested_floor)
    
    # Moving away or opposite direction
    return 99
```

### Error Messages
- Door operation in UP/DOWN state: "Cannot operate door while elevator is moving. Current state: {state}"
- State transition with open doors: "Cannot move elevator with doors not fully closed. Current door state: {door_state}"
- Floor out of range: "Floor {floor} is out of range. Building has {total_floors} floors (1-{total_floors})"
- Elevator not found: "Elevator {elevator_id} not found"
- Invalid state transition: "Invalid state transition from {current_state} to {new_state}"

## 9. Future Enhancements (Out of Scope for MVP)

- Energy optimization mode (reduce unnecessary movements)
- Load capacity tracking and weight limits
- Express elevators (skip certain floors)
- Elevator groups (e.g., floors 1-10 vs 11-20)
- Historical analytics and performance metrics
- WebSocket support for real-time elevator position updates
- Emergency mode and priority requests
- Database persistence with SQLAlchemy + Alembic migrations

