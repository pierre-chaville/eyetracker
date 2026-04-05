## Eyetracker App Documentation

This document describes the application architecture, user workflows, eye-tracking
communication flow, calibration, data model, backend, and frontend structure.

### Architecture Overview

- **Frontend**: Vue app under `frontend/` with views for communication, keyboard, and eye tracking.
- **Backend**: FastAPI app under `backend/app/` with routers, services, models, and schemas.
- **Database**: SQLite via SQLModel (`backend/app/database.py`).
- **Real-time**: WebSocket endpoint `/ws/speech-to-text` for speech-to-text event streaming.
- **Launcher**: Python/Tkinter app under `launcher/` to start/stop services and open the UI.
- **Desktop shell (Windows)**: `host/IrisWebView2/` — a small .NET 8 WinForms + **WebView2** window that loads the Vite URL, borderless maximized, and closes when the app sends a host message (reliable **Exit** on touch kiosks). See [`launcher/README.md`](../launcher/README.md) for behavior, build steps, and fallbacks.

Backend structure:

- `backend/app/main.py`: FastAPI app factory, middleware, router registration.
- `backend/app/routers/`: HTTP + WS endpoints (thin).
- `backend/app/services/`: Business logic and external integrations.
- `backend/app/models/`: SQLModel DB tables only.
- `backend/app/schemas/`: Pydantic API models (Create/Read/Update).
- `backend/app/utils/`: Helpers and shared exceptions.

### User Workflow

1. **Open app**: User lands on home/dashboard (typically via the launcher’s **Open Browser** / WebView2 host or a browser).
2. **Calibration**: User calibrates eye tracking (optional but recommended).
3. **Communication**:
   - User starts speech-to-text.
   - Caregiver speech is transcribed and streamed to the UI.
   - User selects choices to respond.
4. **Keyboard**:
   - User types with gaze selections.
   - LLM suggests words and completions.
5. **TTS playback**:
   - Selected text is spoken aloud using TTS.

### Eye-Tracking Communication Flow

- **Choice generation**:
  - Frontend requests `/api/communication/choices` with context and history.
  - Backend uses `LLMService` to generate 2–8 choices with probabilities.
  - Choices are stored as `SessionStep` if a session is active.
- **Choice selection**:
  - Frontend posts `/api/communication/select`.
  - Backend generates TTS audio and optionally updates the session step.
  - Playback runs asynchronously (pygame only).

### Calibration

Calibration computes gaze offsets and affine coefficients:

- Collect gaze samples at known targets.
- Compute robust averages with geometric median.
- Estimate affine coefficients (weighted least squares).
- Persist calibration JSON on the user record.

Endpoint:
- `POST /api/calibration/process` with `CalibrationRequest`.

### Data Model (DB)

Tables in `backend/app/models/`:

- **User**
  - Stores configuration, calibration JSON, notes, and voice settings.
- **Caregiver**
  - Stores caregiver profiles.
- **CommunicationSession**
  - Session record linked to user/caregiver.
- **SessionStep**
  - Step records with choices and selected text.

### API Schemas (Create/Read/Update)

Schemas in `backend/app/schemas/` follow:

- `UserCreate`, `UserRead`, `UserUpdate`
- `CaregiverCreate`, `CaregiverRead`, `CaregiverUpdate`
- `CommunicationSessionCreate`, `CommunicationSessionRead`, `CommunicationSessionUpdate`
- `SessionStepCreate`, `SessionStepRead`
- Plus request/response schemas for communication, keyboard, config, and general status.

### Backend Details

Key endpoints (non-exhaustive):

- **General**
  - `GET /` → status
  - `GET /api/health`
- **Users**
  - `GET /api/users`
  - `POST /api/users`
  - `PUT /api/users/{id}`
  - `DELETE /api/users/{id}`
- **Caregivers**
  - `GET /api/caregivers`
  - `POST /api/caregivers`
  - `PUT /api/caregivers/{id}`
  - `DELETE /api/caregivers/{id}`
- **Communication**
  - `POST /api/communication/choices`
  - `POST /api/communication/select`
  - `POST /api/communication/sessions`
  - `GET /api/communication/sessions`
  - `GET /api/communication/sessions/{id}`
  - `PUT /api/communication/sessions/{id}`
  - `DELETE /api/communication/sessions/{id}`
- **Keyboard**
  - `POST /api/keyboard/predictions`
  - `POST /api/keyboard/tts`
- **Calibration**
  - `POST /api/calibration/start`
  - `POST /api/calibration/process`
- **Speech-to-Text**
  - `POST /api/speech-to-text/start`
  - `POST /api/speech-to-text/stop`
  - `GET /api/speech-to-text/status`
  - `WS /ws/speech-to-text`

Speech-to-text WebSocket events:

- `connected`
- `speech_started`
- `transcription`
- `error`

### Frontend Details

Key views:

- `frontend/src/views/Communicate.vue`
  - Speech-to-text control and communication grid.
  - WebSocket connection to `/ws/speech-to-text`.
- `frontend/src/views/Keyboard.vue`
  - Predictive keyboard with LLM suggestions.
- `frontend/src/views/EyeTracking.vue`
  - Eye tracking calibration and status UI.

Eye-tracking WebSocket (frontend only):

- Implemented in `frontend/src/composables/useEyeTracking.js`.
- Defaults to `ws://127.0.0.1:8765` (configurable).

### External Integrations

- **LLM**: OpenAI / Anthropic via LangChain.
- **TTS**: pyttsx3 (offline), OpenAI, ElevenLabs, Google TTS.
- **STT**: Deepgram SDK (microphone streaming).

### Running the Backend

Entry point:

- `backend/main.py` (wraps `app.main`)

Recommended run:

- `uvicorn app.main:app --reload --port 8080`

