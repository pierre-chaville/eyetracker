# Backend compliance audit vs `.cursor/rules/backend.md`

This document audits the backend against the rules in `.cursor/rules/backend.md` and lists compliant areas and gaps with concrete references.

---

## Compliant areas

- **Stack** — FastAPI, SQLModel, SQLite via aiosqlite, LangChain, WebSocket, Python 3.11+.
- **Project structure** — `app/main.py`, `config.py`, `database.py`, `dependencies.py`, `models/`, `schemas/`, `routers/`, `services/`, `chains/`, `utils/`; routers by domain; prefix `/api/v1`.
- **Lifespan** — `main.py` uses `@asynccontextmanager` for startup (DB, httpx client) and shutdown (client cleanup, STT stop).
- **Global exception handler** — `main.py` registers `_global_exception_handler` for `Exception`; returns 500 with safe message and correlation id; logs full traceback.
- **Database** — `database.py`: `create_async_engine` with `sqlite+aiosqlite`, `AsyncSession`, `async_sessionmaker`. `get_session()` yields `AsyncSession`. WAL enabled: `PRAGMA journal_mode=WAL` in `create_db_and_tables`. Services use `select()` and async session methods (no raw SQL in business logic).
- **Layered architecture** — Routers are thin (validate, call service, return). Business logic in services. Models are table-only (`table=True`); schemas are separate (e.g. `UserCreate`, `UserRead`, `UserUpdate`). No HTTP concepts in services.
- **Routers** — Explicit `response_model` on endpoints; creation endpoints use `status_code=status.HTTP_201_CREATED` (users, caregivers, communication sessions/steps, keyboards). `tags` on routers. `HTTPException` only in routers; domain exceptions raised in services and converted in routers.
- **Domain exceptions** — `app/utils/exceptions.py`: `EntityNotFoundError`, `ConfigValidationError`, `ConfigSaveError`, `SpeechToTextUnavailableError`, `SpeechToTextOperationError`. Routers catch and map to HTTP (e.g. `users.py`, `communication.py`, `config.py`, `speech_to_text.py`).
- **Dependency injection (session)** — `dependencies.py` provides `get_session`, `get_user_service`, `get_caregiver_service`, `get_session_service`, `get_communication_service`, `get_keyboard_service`, `get_keyboard_layout_service`, `get_config_service`. Services receive `AsyncSession` via constructor.
- **No `requests`** — External HTTP uses `httpx` (e.g. TTS ElevenLabs in `services/tts.py`).
- **No `print()`** — Codebase uses `get_logger()` and structured logging.
- **StrEnum** — `app/types.py`: `SpeechEventType(StrEnum)` for WebSocket event types.
- **Pathlib** — Config and TTS cache use `pathlib.Path` (e.g. `config.py`, `tts.py`); a few spots in TTS still use `os.path`/`os` (see gaps).
- **WebSocket** — Single STT WebSocket at `/ws/speech-to-text`; `try/finally` with `broadcaster.disconnect(websocket)`; typed envelope with `type` and `data`; connection manager pattern (`WebSocketBroadcaster`).
- **LangChain** — Prompts in `chains/prompts.py`; LCEL in `chains/choices_chain.py`; clear input/output schemas (`ChoicesChainInput`, `ChoicesOutput`); chains used from `LLMService`.
- **Async I/O** — Endpoints are `async def`; DB-using services are async; STT start/stop wrapped in `asyncio.to_thread()` in router.
- **Naming** — Files `snake_case`, classes `PascalCase`, routers by domain, routes under `/api/v1`.

---

## Gaps and non-compliance

### 1. Dependency injection: globals instead of injectable deps (High)

**Rule:** “Services receive their dependencies via constructor or function params, never import globals. External API clients (TTS, STT, LLM) must be injectable and mockable.”

**Current:**

- **Settings:** Services and utils call `get_settings()` (e.g. `tts.py`, `stt.py`, `llm.py`, `config.py`, `retry.py`, `main.py` lifespan) instead of receiving a settings object via constructor or `Depends`.
- **HTTP client:** `services/tts.py` uses `get_httpx_client()` from `app.http_client` instead of receiving an `httpx.AsyncClient` (or factory) via constructor.
- **LLM/TTS:** `CommunicationService` and `KeyboardService` call `get_llm_service()` and `get_tts_service()` inside methods instead of receiving `LLMService`/`TTSService` (or factories) via constructor. Same for `get_current_speech_to_text_service()`.

**Change:** Add `Depends(get_settings)` (or a settings factory) and inject settings into service constructors. Inject `httpx.AsyncClient` (or a shared client from app state) into TTS (and any other HTTP-based service). Add `get_llm_service` / `get_tts_service` (or factory) in `dependencies.py` and inject `LLMService` and `TTSService` into `CommunicationService` and `KeyboardService` via constructor. Avoid module-level `get_*_service()` inside services so tests can inject mocks.

---

### 2. `time.sleep()` (High)

**Rule:** “Never use `time.sleep()` — use `asyncio.sleep()`.”

**Current:** `backend/app/services/stt.py` line 181: `time.sleep(0.1)` (used in a sync thread before starting the stream thread).

**Change:** If this must run in a thread, keep it but document; otherwise use a small `threading.Event.wait(timeout=0.1)` or run the blocking flow in a thread via `asyncio.to_thread()` and use `await asyncio.sleep(0.1)` in async code where the rule applies.

---

### 3. `pathlib` vs `os.path` / `os` (Low)

**Rule:** “Use `pathlib.Path` instead of `os.path`.”

**Current:** `backend/app/services/tts.py`: `os.path.exists(tmp_path)`, `os.unlink(tmp_path)` (e.g. around lines 174, 420, 446), and `open(tmp_path, ...)` where `tmp_path` is from `tempfile.NamedTemporaryFile`.

**Change:** Use `Path(tmp_path).exists()`, `Path(tmp_path).unlink(missing_ok=True)`, and pathlib-based open where it keeps code clear.

---

### 4. Hardcoded `DATABASE_URL` (Medium)

**Rule:** “Never hardcode API keys, file paths, or URLs.”

**Current:** `backend/app/database.py` line 14: `DATABASE_URL = "sqlite+aiosqlite:///./eyetracker.db"`.

**Change:** Read from settings (e.g. `Settings.database_url` or `Settings.sqlite_path`) with a default; load via `BaseSettings`/env.

---

### 5. WebSocket manager in app state (Low)

**Rule:** “The manager must be a singleton (or app-state bound via `app.state`) — never instantiate per-request.”

**Current:** `routers/speech_to_text.py`: `WebSocketBroadcaster` is a module-level singleton (`_broadcaster`), not stored on `app.state`.

**Change:** Instantiate the broadcaster in lifespan, set `app.state.ws_broadcaster = ...`, and provide it via a dependency that reads from `request.app.state`. This makes the singleton explicit and testable.

---

### 6. `except Exception` without logging (Medium)

**Rule:** “Never catch bare `except:` or `except Exception:` without logging.”

**Current:** Most `except Exception:` blocks in the codebase do call `logger.exception(...)` (e.g. `communication.py`, `keyboard.py`, `speech_to_text` router). A few in `services/speech_to_text.py` (e.g. callbacks around 65, 85, 101) and similar helpers catch and re-raise or pass; ensure every such handler at least logs (e.g. `logger.exception` or `logger.debug`) so failures are visible.

**Change:** Audit all `except Exception:` (and bare `except:`) and add `logger.exception(...)` (or appropriate level with `exc_info=True`) where missing.

---

### 7. Config vs settings naming (Low)

**Rule:** “config.py — Settings via pydantic-settings (BaseSettings).”

**Current:** Env-derived settings live in `settings.py` (`BaseSettings`); file-based user config (prompts, UI, etc.) lives in `config.py` and is loaded from JSON. So “config” in the rule is satisfied by having a `BaseSettings`-based layer; the file-based layer is an extra.

**Change:** Optional. Rename or document: e.g. “Env settings in `settings.py`; user config file in `config.py`” so the split is clear and the rule is satisfied by `settings.py`.

---

### 8. Optional: LLM response caching (Low)

**Rule:** “Cache LLM responses where appropriate (same context → same prediction).”

**Current:** No caching in `LLMService.generate_choices()`.

**Change:** Add an optional in-memory (or Redis) cache keyed by (system_prompt, context, conversation_history hash) and reuse cached result when present.

---

### 9. Optional: Circuit breaker for external APIs (Low)

**Rule:** “Implement circuit breaker pattern for non-critical APIs (TTS/STT) to avoid cascading failures.”

**Current:** Retry and timeout exist (e.g. `utils/retry.py`); no circuit breaker.

**Change:** Add a small circuit breaker (e.g. tenacity or custom) around TTS/STT (and optionally LLM) so repeated failures stop calling the API for a short period.

---

## Summary table

| Area                         | Status        | Priority |
|-----------------------------|---------------|----------|
| Async DB, WAL, AsyncSession | Compliant     | —        |
| Router prefix `/api/v1`     | Compliant     | —        |
| response_model / 201 / tags | Compliant     | —        |
| Domain exceptions + handler | Compliant     | —        |
| No requests / no print      | Compliant     | —        |
| StrEnum, pathlib (mostly)   | Compliant     | —        |
| Injectable TTS/STT/LLM/settings/client | Non-compliant | High     |
| No `time.sleep()`           | Non-compliant | High     |
| pathlib everywhere (TTS)    | Partial       | Low      |
| DATABASE_URL from settings | Non-compliant | Medium   |
| WS manager on app.state     | Partial       | Low      |
| Except Exception + logging | Mostly OK     | Medium   |
| LLM cache / circuit breaker | Not done      | Low      |

Recommended order of work: (1) Make TTS/STT/LLM and HTTP client and settings injectable via Depends/constructors; (2) Remove or replace `time.sleep` and add missing exception logging; (3) Move `DATABASE_URL` to settings and WebSocket manager to `app.state`; (4) Replace remaining `os.path`/`os` in TTS with pathlib; (5) Optionally add LLM cache and circuit breaker.
