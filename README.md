# Eye Tracker – Communication Assistant for Rett Syndrome

An application that uses eye tracking and AI (LLMs) to assist people with Rett syndrome in communicating through eye gaze.

## Architecture

- **Frontend**: Vue.js 3 with Tailwind CSS and Headless UI (port 5173)
- **Backend**: Python FastAPI with uvicorn (port 8080)
- **Bridge**: C# .NET 8 Tobii gaze WebSocket server (port 8765)
- **Launcher**: Python Tkinter desktop GUI to manage all services

## Project Structure

```
eyetracker/
├── backend/           # Python FastAPI backend
├── bridge/            # C# Tobii eye-tracker WebSocket bridge
├── frontend/          # Vue.js frontend application
├── launcher/          # Desktop launcher (start/stop/update)
├── docs/              # Documentation
└── package.json       # Convenience npm scripts
```

## Quick Start

### Using the Launcher (recommended)

Double-click `launcher/start.bat` or run:

```bash
python launcher/launcher.py
```

The launcher provides buttons to start/stop each service, update via git, and open the browser.

### Manual Setup

#### Prerequisites

- Python 3.9+
- Node.js 18+
- .NET 8 SDK (for the Tobii bridge, optional)

#### Installation

1. Create and activate a Python virtual environment:
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. (Optional) Build the C# bridge:
```bash
cd bridge
dotnet build
```

#### Running

Start each component in a separate terminal:

```bash
# Backend
cd backend
python -m uvicorn main:app --reload --port 8080

# Frontend
cd frontend
npm run dev

# Bridge (needs Tobii hardware)
cd bridge
dotnet run
```

Then open http://localhost:5173 in your browser.

## Features

- Eye tracking integration (Tobii via C# bridge)
- AI-powered communication choices (OpenAI / Anthropic)
- AAC pictogram support (ARASAAC)
- Predictive keyboard with gaze input
- Speech-to-text (Deepgram) and text-to-speech (OpenAI / ElevenLabs / Google / pyttsx3)
- Calibration system with gaze mapping
- Communication session history and analysis
- Multi-language support (English / French)

## License

MIT
