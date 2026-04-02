# Eye Tracker Station – Launcher

Desktop GUI (Python / Tkinter) to manage all components of the eye-tracking app.

## Quick start

Double-click **`start.bat`**, or run from a terminal:

```bash
cd launcher
python launcher.py
```

## Features

| Button | Action |
|--------|--------|
| **Launch All** | Starts Backend, Frontend, and Bridge in order |
| **Stop All** | Gracefully stops every running service |
| **Update** | `git pull` → `pip install` → `npm install` → `dotnet build` |
| **Open Browser** | Opens `http://localhost:5173` in the default browser |
| **Clear Log** | Clears the log panel |
| Per-service **Start / Stop** | Toggle individual services |

## Services managed

| Service | Stack | Default port |
|---------|-------|-------------|
| Backend | Python FastAPI (uvicorn) | 8080 |
| Frontend | Vue 3 / Vite | 5173 |
| Bridge | C# .NET 8 (Tobii) | 8765 |

## Requirements

- Python 3.9+ with Tkinter (included in standard Windows installs)
- The backend virtualenv at `backend/venv/` (falls back to system Python)
- Node.js / npm for the frontend
- .NET 8 SDK for the bridge (optional if bridge is not used)
