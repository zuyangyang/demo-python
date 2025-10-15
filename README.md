## Demo Python API (FastAPI)

Minimal FastAPI "Hello, World" scaffold with tests and `uv` workflows.

### Prerequisites
- Python 3.10+
- uv installed

### Install
```bash
uv venv
uv sync
```

### Run (development)
```bash
uv run uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/api/v1/hello`.

### Test
```bash
uv run pytest -q
```

### Structure
```
app/
  api/v1/endpoints/hello.py
  api/v1/router.py
  core/config.py
  main.py
  schemas/hello.py
  tests/
```

### API
- GET `/api/v1/hello` → `{ "message": "Hello, World" }`
  - Optional query `name` to personalize the greeting


