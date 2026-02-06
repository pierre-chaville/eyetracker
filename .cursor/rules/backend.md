---
description: Rules for backend Python code (FastAPI, SQLModel, APIs)
globs: backend/**/*.py
alwaysApply: false
---

# Backend — FastAPI Eyetracking App

## Stack
- **Framework**: FastAPI (async by default)
- **ORM**: SQLModel (SQLAlchemy + Pydantic hybrid)
- **Database**: SQLite (via aiosqlite for async)
- **LLM**: LangChain
- **APIs**: Speech-to-Text (STT), Text-to-Speech (TTS), LLM
- **Python**: 3.12+

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory, lifespan, middleware
│   ├── config.py            # Settings via pydantic-settings (BaseSettings)
│   ├── database.py          # Engine, session factory, get_session dependency
│   ├── dependencies.py      # Shared FastAPI dependencies
│   ├── models/              # SQLModel table models (DB schema)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── session.py       # Eye-tracking session model
│   │   └── ...
│   ├── schemas/             # Pydantic models for API request/response
│   │   ├── __init__.py
│   │   └── ...
│   ├── routers/             # FastAPI APIRouter modules
│   │   ├── __init__.py
│   │   ├── tracking.py
│   │   ├── tts.py
│   │   ├── stt.py
│   │   ├── llm.py
│   │   └── ...
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── tracking.py
│   │   ├── tts_service.py
│   │   ├── stt_service.py
│   │   ├── llm_service.py
│   │   └── ...
│   ├── chains/              # LangChain chains and prompts
│   │   ├── __init__.py
│   │   ├── prediction.py
│   │   └── ...
│   └── utils/               # Helpers, constants, enums
│       ├── __init__.py
│       └── ...
├── tests/
├── alembic/                 # DB migrations (if needed)
└── pyproject.toml
```

## Architecture Rules

### Layered Architecture (strict separation)
- **Routers** → thin HTTP layer. Validate input, call service, return response. No business logic.
- **Services** → all business logic. Receive typed params, return typed results. No HTTP concepts (no Request, Response, status codes).
- **Models** → SQLModel table definitions only. No methods with business logic.
- **Schemas** → Pydantic models for API contracts. Separate from DB models even if fields overlap.

### Dependency Injection
- Use FastAPI `Depends()` for session, config, and services.
- Services receive their dependencies via constructor or function params, never import globals.
- External API clients (TTS, STT, LLM) must be injectable and mockable.

```python
# Good
async def get_llm_service(session: AsyncSession = Depends(get_session)) -> LLMService:
    return LLMService(session=session, config=get_settings())

@router.post("/predict")
async def predict(request: PredictRequest, service: LLMService = Depends(get_llm_service)):
    return await service.predict(request.context)
```

## Coding Standards

### General Python
- Type hints on ALL function signatures and return types. No `Any` unless truly unavoidable.
- Use `async def` for all endpoints and all I/O-bound functions (DB, API calls).
- Use `pathlib.Path` instead of `os.path`.
- Use `logging` module with structured messages, never `print()`.
- Use `enum.StrEnum` for string enums (status codes, event types, etc.).
- Google-style docstrings for public functions and classes.
- Max line length: 100 characters.
- Use f-strings for formatting.

### FastAPI Specifics
- Always define explicit `response_model` on endpoints.
- Always define explicit `status_code` on creation endpoints (201).
- Use `HTTPException` only in routers, never in services. Services raise custom domain exceptions, routers catch and convert.
- Use `tags` on all routers for OpenAPI grouping.
- Use lifespan context manager for startup/shutdown (DB init, API client warmup, cleanup).

```python
# Custom exceptions in services
class EntityNotFoundError(Exception):
    def __init__(self, entity: str, id: int):
        self.entity = entity
        self.id = id

# Router catches and converts
@router.get("/{session_id}", response_model=SessionRead)
async def get_session(session_id: int, service: TrackingService = Depends(get_tracking_service)):
    try:
        return await service.get_session(session_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"{e.entity} {e.id} not found")
```

### SQLModel / Database
- Separate **table models** (`table=True`) from **schema models** (plain SQLModel or Pydantic).
- Use the Create/Read/Update pattern for schemas: `SessionCreate`, `SessionRead`, `SessionUpdate`.
- `SessionUpdate` fields should all be `Optional` for partial updates.
- Always use `select()` statements, never raw SQL strings.
- Use `AsyncSession` with `aiosqlite` — never blocking calls.
- Wrap write operations in explicit transactions.
- Define indexes on frequently queried columns.
- Use `relationship()` with care — prefer explicit joins in services for complex queries.
- Enable WAL mode for SQLite concurrency: `PRAGMA journal_mode=WAL`.

```python
# Model pattern
class SessionBase(SQLModel):
    name: str
    user_id: int
    status: SessionStatus = SessionStatus.ACTIVE

class Session(SessionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SessionCreate(SessionBase):
    pass

class SessionRead(SessionBase):
    id: int
    created_at: datetime
    updated_at: datetime

class SessionUpdate(SQLModel):
    name: str | None = None
    status: SessionStatus | None = None
```

### External API Integration (STT, TTS, LLM)

- Each external API gets its own service class with a well-defined interface (Protocol or ABC).
- NEVER call external APIs directly from routers.
- All API calls must have: timeout, retry logic (tenacity), and proper error handling.
- Use `httpx.AsyncClient` for HTTP calls, not `requests`.
- Store API keys in config (`BaseSettings` with env vars), never hardcoded.
- Implement circuit breaker pattern for non-critical APIs (TTS/STT) to avoid cascading failures.
- Cache LLM responses where appropriate (same context → same prediction).
- Log all external API calls with timing for debugging latency issues.

```python
class STTService:
    """Speech-to-Text service wrapper."""

    def __init__(self, client: httpx.AsyncClient, config: Settings):
        self._client = client
        self._config = config

    async def transcribe(self, audio: bytes, language: str = "fr") -> TranscriptionResult:
        """Transcribe audio bytes to text."""
        ...
```

### LangChain Specifics
- Keep prompts in dedicated files or constants, not inline in chain logic.
- Use LCEL (LangChain Expression Language) for chain composition.
- Define clear input/output schemas for every chain.
- Use callbacks for logging/tracing, not print statements.
- Keep chains stateless — pass all required context explicitly.
- Prefer `| RunnablePassthrough` patterns over complex `SequentialChain`.

### Error Handling
- Define a hierarchy of domain exceptions in `app/utils/exceptions.py`.
- Services raise domain exceptions, routers convert to HTTP responses.
- Use a global exception handler for unhandled errors (return 500 with safe message, log full traceback).
- All async operations must be wrapped in try/except — never let exceptions silently disappear.
- External API failures must be handled gracefully with user-friendly fallbacks.

### Testing
- Use `pytest` + `pytest-asyncio` + `httpx.AsyncClient` for async test client.
- Use an in-memory SQLite database for tests.
- Mock all external APIs (STT, TTS, LLM) in tests — never call real APIs.
- Service-level tests for business logic, router-level tests for HTTP contracts.
- Name test files `test_<module>.py`, test functions `test_<behavior>`.

### Performance & Concurrency
- SQLite is single-writer: use a write lock or queue for concurrent write operations.
- Offload CPU-heavy tasks (audio processing) to `asyncio.to_thread()` or a background task queue.
- Use `BackgroundTasks` for fire-and-forget operations (logging events, cleanup).
- Stream LLM responses where possible using `StreamingResponse`.

## Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Routers: named by domain (`tracking.py`, `tts.py`), prefix = `/api/v1/<domain>`

## Things to NEVER Do
- Never use `requests` library (blocking) — use `httpx` async.
- Never use `time.sleep()` — use `asyncio.sleep()`.
- Never put business logic in routers.
- Never hardcode API keys, file paths, or URLs.
- Never use `SELECT *` equivalent — always select specific fields when possible.
- Never catch bare `except:` or `except Exception:` without logging.
- Never return raw SQLModel table instances from endpoints — always use Read schemas.
- Never use synchronous SQLModel session in async context.