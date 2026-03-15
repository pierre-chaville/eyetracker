from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.http_client import set_httpx_client
from app.routers import (
    calibration,
    caregivers,
    communication,
    config,
    eye_tracking,
    general,
    keyboards,
    keyboard,
    speech_to_text,
    users,
)
from app.services.speech_to_text import get_current_speech_to_text_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan for startup and shutdown tasks."""
    await create_db_and_tables()
    from app.settings import get_settings

    timeout = get_settings().http_timeout_seconds
    async with httpx.AsyncClient(timeout=timeout) as client:
        set_httpx_client(client)
        try:
            yield
        finally:
            set_httpx_client(None)
    speech_service = get_current_speech_to_text_service()
    if speech_service:
        speech_service.stop()


app = FastAPI(title="Eye Tracker API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(general.router)
app.include_router(eye_tracking.router)
app.include_router(communication.router)
app.include_router(keyboard.router)
app.include_router(keyboards.router)
app.include_router(users.router)
app.include_router(caregivers.router)
app.include_router(config.router)
app.include_router(calibration.router)
app.include_router(speech_to_text.router)
