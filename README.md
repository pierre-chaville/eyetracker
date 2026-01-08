# Eye Tracker - Communication Assistant for Rett Syndrome

An Electron-based application that uses eye tracking and AI (LLMs) to assist people with Rett syndrome in communicating through eye gaze.

## Architecture

- **Frontend**: Vue.js 3 with Tailwind CSS and Headless UI
- **Backend**: Python FastAPI
- **Desktop Framework**: Electron

## Project Structure

```
eyetracker/
├── electron/          # Electron main process files
├── frontend/          # Vue.js frontend application
├── backend/           # Python FastAPI backend
└── package.json       # Root package.json for Electron
```

## Setup

### Prerequisites

- Node.js (v18 or higher)
- Python 3.9 or higher
- npm or yarn

### Installation

1. Install all dependencies:
```bash
npm run install:all
```

This will install:
- Node.js dependencies (root)
- Frontend dependencies (Vue.js, Tailwind, etc.)
- Python dependencies (FastAPI, etc.)

2. Create a Python virtual environment (recommended):
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

## Development

Run the application in development mode:

```bash
npm run dev
```

This will:
1. Start the Vue.js dev server (http://localhost:5173)
2. Start the FastAPI backend (http://localhost:8000)
3. Launch the Electron app

### Individual Commands

- Frontend only: `npm run dev:frontend`
- Backend only: `npm run dev:backend`
- Electron only: `npm start` (after frontend/backend are running)

## Building

Build the application for production:

```bash
npm run build
```

## Features

- Eye tracking integration
- AI-powered language assistance
- Accessible UI design
- Calibration system
- Communication history

## License

MIT

