from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Set

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.schemas import MessageResponse, SpeechToTextStatusResponse
from app.services.speech_to_text import SpeechEventBroadcaster, SpeechToTextManager
from app.utils.exceptions import SpeechToTextOperationError, SpeechToTextUnavailableError
from app.utils.logging import get_logger

logger = get_logger()
router = APIRouter(tags=["speech-to-text"])


class WebSocketBroadcaster(SpeechEventBroadcaster):
    """Broadcast speech events to connected WebSocket clients."""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    @property
    def connections_count(self) -> int:
        return len(self._connections)

    async def broadcast(self, event_type: str, data: dict) -> None:
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.info(
            "Broadcasting speech event",
            extra={"event_type": event_type, "connections": len(self._connections)},
        )
        disconnected = set()
        for connection in self._connections.copy():
            try:
                await connection.send_json(message)
                logger.debug(
                    "Sent speech event to WebSocket client",
                    extra={"event_type": event_type},
                )
            except Exception:
                logger.exception("Failed to send speech event", extra={"event_type": event_type})
                disconnected.add(connection)
        self._connections.difference_update(disconnected)
        logger.info(
            "Active WebSocket connections updated",
            extra={"connections": len(self._connections)},
        )

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)


_broadcaster = WebSocketBroadcaster()


def get_broadcaster() -> WebSocketBroadcaster:
    return _broadcaster


def get_speech_to_text_manager(
    broadcaster: WebSocketBroadcaster = Depends(get_broadcaster),
) -> SpeechToTextManager:
    return SpeechToTextManager(broadcaster)


@router.websocket("/ws/speech-to-text")
async def websocket_speech_to_text(
    websocket: WebSocket,
    broadcaster: WebSocketBroadcaster = Depends(get_broadcaster),
) -> None:
    """WebSocket endpoint for speech-to-text events."""
    await broadcaster.connect(websocket)
    logger.info(
        "WebSocket client connected",
        extra={"connections": broadcaster.connections_count},
    )
    await websocket.send_json(
        {
            "type": "connected",
            "data": {"message": "WebSocket connected"},
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    try:
        while True:
            try:
                data = await websocket.receive_text()
                await websocket.send_json({"type": "pong", "data": data})
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WebSocket error")
    finally:
        broadcaster.disconnect(websocket)
        logger.info(
            "WebSocket client disconnected",
            extra={"connections": broadcaster.connections_count},
        )


@router.post("/api/speech-to-text/start", response_model=MessageResponse)
async def start_speech_to_text(
    manager: SpeechToTextManager = Depends(get_speech_to_text_manager),
) -> MessageResponse:
    """Start speech-to-text transcription (runs in thread to avoid blocking)."""
    try:
        return await asyncio.to_thread(manager.start)
    except SpeechToTextUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.detail,
        ) from exc
    except SpeechToTextOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.detail,
        ) from exc


@router.post("/api/speech-to-text/stop", response_model=MessageResponse)
async def stop_speech_to_text(
    manager: SpeechToTextManager = Depends(get_speech_to_text_manager),
) -> MessageResponse:
    """Stop speech-to-text transcription (runs in thread to avoid blocking)."""
    try:
        return await asyncio.to_thread(manager.stop)
    except SpeechToTextOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.detail,
        ) from exc


@router.get("/api/speech-to-text/status", response_model=SpeechToTextStatusResponse)
async def get_speech_to_text_status(
    manager: SpeechToTextManager = Depends(get_speech_to_text_manager),
) -> SpeechToTextStatusResponse:
    """Get speech-to-text status."""
    return manager.status()
