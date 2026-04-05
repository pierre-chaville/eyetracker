# Eye Tracker Station – Launcher

Desktop GUI (Python / Tkinter) to manage all components of the eye-tracking app.

## Quick start

Double-click **`start.bat`**, or run from a terminal:

```bash
cd launcher
python launcher.py
```

Start **Backend** and **Frontend** (and **Bridge** if you use Tobii), then use **Open Browser** to open the UI.

## Features

| Button | Action |
|--------|--------|
| **Launch All** | Starts Backend, Frontend, and Bridge in order |
| **Stop All** | Gracefully stops every running service |
| **Update** | `git pull` → `pip install` → `npm install` → `dotnet build` (bridge) |
| **Open Browser** | Opens the UI at `http://localhost:5173` (see [Desktop shell](#desktop-shell-windows) below) |
| **Clear Log** | Clears the log panel |
| **Shutdown** | Stops services and schedules a system shutdown (with confirmation) |
| Per-service **Start / Stop** | Toggle individual services |

## Services managed

| Service | Stack | Default port |
|---------|-------|--------------|
| Backend | Python FastAPI (uvicorn) | 8080 |
| Frontend | Vue 3 / Vite | 5173 |
| Bridge | C# .NET 8 (Tobii WebSocket) | 8765 |

## Desktop shell (Windows)

On **Windows**, **Open Browser** prefers the **WebView2 host** in `host/IrisWebView2/`:

1. If `host/IrisWebView2/bin/Release/net8.0-windows/IrisWebView2.exe` exists, it is launched with the dev URL as an argument (fastest).
2. Otherwise the **Debug** build exe, if present.
3. Otherwise `dotnet run --project host/IrisWebView2/IrisWebView2.csproj` (first run may compile).

The host opens a **borderless, maximized** window (no title bar). The Vue app’s **Exit** action asks the host to close the process via `postMessage`, which works reliably on touch/kiosk setups.

If the WebView2 project is missing or `dotnet` fails to start it, the launcher falls back to **Chrome or Edge** in `--app` fullscreen mode, then to the system default browser.

### One-time host build (recommended)

From the repository root:

```bash
dotnet build -c Release host/IrisWebView2/IrisWebView2.csproj
```

### WebView2 Runtime

The Evergreen **WebView2 Runtime** must be installed (it is preinstalled on many Windows 11 images). If the host shows an error on launch, install the runtime from [Microsoft’s WebView2 page](https://developer.microsoft.com/microsoft-edge/webview2/).

## Requirements

- Python 3.9+ with Tkinter (included in standard Windows installs)
- The backend virtualenv at `backend/venv/` (falls back to system Python)
- Node.js / npm for the frontend
- .NET 8 SDK for the **bridge** and for the **WebView2 host** on Windows
- **WebView2 Runtime** on Windows when using the host (see above)

## Non-Windows

**Open Browser** uses Chrome/Edge `--app` or `webbrowser` when the WebView2 project path is not used (the host targets Windows only).
