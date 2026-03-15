from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import create_db_and_tables
from app.utils.logging import get_logger
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


logger = get_logger(__name__)


def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log full traceback and return 500 with safe message."""
    correlation_id = str(uuid.uuid4())[:8]
    logger.exception(
        "Unhandled exception (correlation_id=%s): %s",
        correlation_id,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "correlation_id": correlation_id,
        },
    )


app = FastAPI(title="Eye Tracker API", version="1.0.0", lifespan=lifespan)

app.add_exception_handler(Exception, _global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_V1_PREFIX = "/api/v1"

app.include_router(general.router, prefix=API_V1_PREFIX)
app.include_router(eye_tracking.router, prefix=API_V1_PREFIX)
app.include_router(communication.router, prefix=API_V1_PREFIX)
app.include_router(keyboard.router, prefix=API_V1_PREFIX)
app.include_router(keyboards.router, prefix=API_V1_PREFIX)
app.include_router(users.router, prefix=API_V1_PREFIX)
app.include_router(caregivers.router, prefix=API_V1_PREFIX)
app.include_router(config.router, prefix=API_V1_PREFIX)
app.include_router(calibration.router, prefix=API_V1_PREFIX)
app.include_router(speech_to_text.router, prefix=API_V1_PREFIX)
