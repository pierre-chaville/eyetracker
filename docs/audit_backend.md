# Backend Compliance Diagnostic vs `backend.md`

This document audits the backend codebase against the rules defined in `.cursor/rules/backend.md` and lists what should be changed to improve compliance.

---

## Compliant Areas

- **Routers** — Most endpoints define explicit `response_model` and `tags`. Creation endpoints use `status_code=201` where checked (users, caregivers, communication, etc.). Routers catch domain exceptions (e.g. `EntityNotFoundError`) and map to `HTTPException`; services do not raise `HTTPException`.
- **Layered architecture** — Routers are thin (validate, call service, return). Business logic lives in services. Models vs schemas are separated (SQLModel tables vs Pydantic schemas); Create/Read/Update pattern is used (e.g. `UserCreate`, `UserRead`, `UserUpdate`).
- **Dependency injection** — Services are injected via `Depends(get_*_service)`; services receive session/deps in constructor.
- **Domain exceptions** — `app/utils/exceptions.py` defines `EntityNotFoundError`, `ConfigValidationError`, `ConfigSaveError`, `SpeechToText*` errors; used in services and converted in routers.
- **Database** — Services use `select()` (no `SELECT *`); no raw SQL in service layer (only in migration helper).
- **Lifespan** — `main.py` uses `@asynccontextmanager` lifespan for startup/shutdown.
- **WebSocket** — Single STT WebSocket; `try/finally` with `broadcaster.disconnect(websocket)`; typed envelope with `type` and `data`.
- **Path / pathlib** — `pathlib.Path` used where paths are handled (e.g. config, TTS cache).
- **Naming** — Files `snake_case`, classes `PascalCase`, routers by domain; routes under `/api/...`.

---

## Non-Compliant or Missing (What to Change)

### 1. Database: Sync and Blocking (Critical)

- **Rule:** Use `AsyncSession` with `aiosqlite` — never blocking DB in async context.
- **Current:** `database.py` uses sync `create_engine` + `Session` (blocking). `get_session()` yields a sync `Session`; all service methods that touch DB are sync.
- **Change:** Switch to `create_async_engine` with `aiosqlite`, `async_sessionmaker`, and `AsyncSession`. Replace `get_session()` with an async dependency that yields `AsyncSession`. Make all DB-using service methods `async def` and use `await session.execute()`, `session.get()`, etc.; routers should `await` service calls.

### 2. Config: Not pydantic-settings (Critical)

- **Rule:** Settings via pydantic-settings (`BaseSettings`), env vars; no hardcoded paths/keys.
- **Current:** `app/config.py` uses a JSON file (`config.json`), `load_config()`/`save_config()`, and `ConfigService`. API keys are read via `os.getenv()` in services (e.g. STT, TTS, LLM) instead of a central settings object.
- **Change:** Add a `BaseSettings`-based settings module (e.g. in `config.py`) for env-derived config (API keys, feature flags, paths). Use it in app and inject where needed. Keep file-based “user config” (prompts, UI preferences) if needed, but load paths/URLs from settings, not hardcoded constants.

### 3. API Prefix `/api/v1/` (Naming)

- **Rule:** Router prefix = `/api/v1/<domain>`.
- **Current:** Routes are `/api/users`, `/api/caregivers`, `/api/health`, etc. (no `v1`).
- **Change:** Register routers with `prefix="/api/v1"` (or use a shared prefix in `main.py`) and use paths like `/api/v1/users`, `/api/v1/caregivers`, etc. Adjust frontend accordingly.

### 4. Creation Endpoints Missing 201

- **Rule:** Explicit `status_code` (201) on creation endpoints.
- **Current:** `routers/keyboards.py` — `POST /api/keyboards` has no `status_code=status.HTTP_201_CREATED`.
- **Change:** Add `status_code=status.HTTP_201_CREATED` to the create-keyboard endpoint (and any other create endpoint that doesn’t have it).

### 5. Async I/O: Endpoints and Services (Critical)

- **Rule:** Use `async def` for all endpoints and all I/O-bound functions (DB, external APIs).
- **Current:** Several routers and services are sync: e.g. `routers/keyboards.py` uses `def list_keyboards`, `def get_keyboard`, etc.; `UserService` methods are sync and use blocking `session.exec()`/`session.get()`/`commit()`.
- **Change:** After moving to `AsyncSession`, make all DB access async and all endpoints `async def` that call services. For any remaining sync I/O (e.g. file or external lib), wrap in `asyncio.to_thread()` where appropriate.

### 6. No `print()`; Use `logging` (High)

- **Rule:** Use `logging` module with structured messages, never `print()`.
- **Current:** Many `print()` calls in `stt.py`, `tts.py`, `calibration.py`, and `speech_to_text.py` (and possibly others).
- **Change:** Replace every `print(...)` with `logger.info(...)` (or appropriate level) and structured `extra={}` where useful. Ensure a single `get_logger()` (or similar) per module.

### 7. No `requests`; Use `httpx` Async (Critical)

- **Rule:** Never use `requests` library (blocking) — use `httpx` async.
- **Current:** `services/tts.py` uses `requests.post()` for ElevenLabs (and possibly others).
- **Change:** Use `httpx.AsyncClient` (injected or created in lifespan), `async with client.post(...)` (or equivalent), with timeout. Make TTS methods async and call them with `await` from routers.

### 8. No `time.sleep()`; Use `asyncio.sleep()` (High)

- **Rule:** Never use `time.sleep()` — use `asyncio.sleep()`.
- **Current:** `services/stt.py` uses `time.sleep(0.1)` (e.g. in a loop).
- **Change:** Replace with `await asyncio.sleep(0.1)` in async code, or run the blocking loop in a thread via `asyncio.to_thread()` and keep the rest of the app async.

### 9. Bare or Broad `except` Without Logging (High)

- **Rule:** Never catch bare `except:` or `except Exception:` without logging.
- **Current:** Multiple `except Exception:` (and similar) with no logger call in `database.py`, `speech_to_text.py`, `communication.py`, `keyboard.py`, `llm.py`, `stt.py`, `routers/speech_to_text.py`.
- **Change:** In every such handler, add at least `logger.exception(...)` (or `logger.error(...)` with exc_info) so failures are visible and debuggable.

### 10. Raw SQL in Migrations (Medium)

- **Rule:** Prefer “always use `select()`”; raw SQL only where necessary (e.g. migrations).
- **Current:** `database.py` uses `text("ALTER TABLE ...")` for schema migration. Rules allow migrations to differ; the “never raw SQL” is mainly for application code.
- **Change:** Keep raw SQL only in migration logic. Prefer a proper migration tool (e.g. Alembic) and move `migrate_database()` into an Alembic migration so app code doesn’t run raw DDL at startup. Optionally enable WAL (see below).

### 11. SQLite WAL Mode (Medium)

- **Rule:** Enable WAL mode for SQLite concurrency: `PRAGMA journal_mode=WAL`.
- **Current:** Not set.
- **Change:** After creating the engine (sync or async), execute `PRAGMA journal_mode=WAL` on the connection (e.g. in lifespan or in a pool connect event) so it applies to all connections.

### 12. External APIs: Timeout, Retry, Injectable Client (High)

- **Rule:** All external API calls must have timeout, retry (e.g. tenacity), proper error handling; use `httpx.AsyncClient`; API keys from config; circuit breaker for non-critical; log calls with timing.
- **Current:** TTS uses `requests` and `timeout=30` but no retry, no circuit breaker, no structured timing logs. STT/TTS/LLM read keys from `os.getenv()` and are not fully injectable/mockable.
- **Change:** Use a single (or per-domain) `httpx.AsyncClient` with timeout; wrap external calls in tenacity retries; add a small circuit breaker for TTS/STT; log each call with duration; inject client and config (with API keys from `BaseSettings`) so tests can mock them.

### 13. String Enums: `StrEnum` (Low)

- **Rule:** Use `enum.StrEnum` for string enums (status codes, event types).
- **Current:** No `StrEnum` usage; status/event types are plain strings (e.g. in WebSocket messages).
- **Change:** Introduce `StrEnum` for event types (e.g. `"stt_partial"`, `"stt_final"`) and for status fields in schemas where appropriate; use them in Pydantic models and WebSocket payloads.

### 14. Global Exception Handler (Medium)

- **Rule:** Use a global exception handler for unhandled errors (return 500 with safe message, log full traceback).
- **Current:** No global handler registered on the FastAPI app.
- **Change:** Add `@app.exception_handler(Exception)` (or a base domain exception) that logs the full traceback and returns a generic 500 response with a safe message and correlation id if desired.

### 15. Project Structure vs Rules (Low)

- **Rule:** Structure mentions `routers/tts.py`, `routers/stt.py`, `routers/ws_stt.py`, `services/tts_service.py`, `stt_service.py`, `ws_manager.py`, `chains/` for LangChain.
- **Current:** Different names: `speech_to_text` router, `stt.py` + `speech_to_text.py` in services, no `chains/` (LLM in `services/llm.py`).
- **Change:** Optional: rename or add aliases so that important entrypoints match the doc (e.g. `ws_stt` for the STT WebSocket, `ws_manager` for the connection manager). Move LangChain logic into `chains/` and keep services thin over chains if you want strict adherence.

### 16. LangChain: Prompts and LCEL (Low)

- **Rule:** Prompts in dedicated files or constants; LCEL for composition; clear input/output schemas; callbacks for logging; stateless chains.
- **Current:** LLM logic lives in `services/llm.py`; prompts may be inline; no `chains/` module.
- **Change:** Extract prompts to constants or files; use LCEL and define input/output Pydantic models; add a `chains/` package and use it from the service; use callbacks for tracing instead of print/log in the middle of chains.

### 17. Type Hints and `Any` (Low)

- **Rule:** Type hints on ALL function signatures and return types; no `Any` unless truly unavoidable.
- **Current:** Models use `Dict[str, Any]` in a few places (e.g. JSON columns); overall type coverage is decent.
- **Change:** Keep improving: replace `Any` with more specific types or TypedDicts where possible; ensure every public function has full type hints.

### 18. Line Length 100 (Low)

- **Rule:** Max line length: 100 characters.
- **Current:** Not verified; a few long lines may exist.
- **Change:** Run a linter/formatter (e.g. Ruff/Black with line length 100) and fix or exclude only where necessary.

### 19. Google-Style Docstrings (Low)

- **Rule:** Google-style docstrings for public functions and classes.
- **Current:** Some modules have docstrings; coverage is uneven.
- **Change:** Add or normalize Google-style docstrings for all public services, routers, and shared utilities.

---

## Summary Table

| Area | Status | Priority |
|------|--------|----------|
| Async DB (aiosqlite, AsyncSession) | Non-compliant | Critical |
| Config (BaseSettings, env) | Non-compliant | Critical |
| No `requests`; use httpx async | Non-compliant | Critical |
| Async endpoints + I/O-bound code | Non-compliant | Critical |
| No `print()`; use logging | Non-compliant | High |
| No `time.sleep()`; use asyncio | Non-compliant | High |
| Except without logging | Non-compliant | High |
| External API retry/timeout/inject | Partial | High |
| Router prefix `/api/v1/` | Non-compliant | Medium |
| Creation 201 on all create routes | Partial (keyboards) | Medium |
| WAL mode SQLite | Missing | Medium |
| Global exception handler | Missing | Medium |
| StrEnum for event/status types | Missing | Low |
| LangChain in chains/, LCEL, prompts | Partial | Low |
| Type hints / docstrings / line length | Partial | Low |

Recommended order of work: (1) async DB + async endpoints and services, (2) config and no-print/no-requests/no-time.sleep + exception logging, (3) httpx + retry/timeout for TTS/STT/LLM, (4) router prefix, 201 on creation, WAL, global handler, then (5) StrEnum, LangChain layout, and docstrings/typing.
