from __future__ import annotations

import asyncio
from typing import Callable, Optional, Protocol, Tuple

from app.schemas import MessageResponse, SpeechToTextStatusResponse
from app.utils.exceptions import SpeechToTextOperationError, SpeechToTextUnavailableError
from app.utils.logging import get_logger

logger = get_logger()

from app.services.stt import SpeechToTextService

_speech_to_text_service: Optional[SpeechToTextService] = None
_event_loop: Optional[asyncio.AbstractEventLoop] = None


class SpeechEventBroadcaster(Protocol):
    @property
    def connections_count(self) -> int:
        """Return active connection count."""

    async def broadcast(self, event_type: str, data: dict) -> None:
        """Broadcast speech events."""


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create event loop for broadcasting events."""
    global _event_loop
    if _event_loop is None or _event_loop.is_closed():
        try:
            _event_loop = asyncio.get_event_loop()
        except RuntimeError:
            _event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_event_loop)
    return _event_loop


def create_speech_callbacks(
    broadcaster: SpeechEventBroadcaster,
) -> Tuple[Callable[[], None], Callable[[str], None], Callable[[str], None]]:
    """Create callbacks for speech events."""

    def on_speech_started() -> None:
        logger.info("Speech started callback invoked")
        try:
            loop = get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    broadcaster.broadcast("speech_started", {}), loop
                )
            else:
                loop.run_until_complete(broadcaster.broadcast("speech_started", {}))
        except Exception:
            logger.exception("Error handling speech started callback")

    def on_transcription(text: str) -> None:
        logger.info("Transcription callback invoked", extra={"text_length": len(text)})
        try:
            loop = get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    broadcaster.broadcast("transcription", {"text": text}), loop
                )
            else:
                loop.run_until_complete(broadcaster.broadcast("transcription", {"text": text}))
        except Exception:
            logger.exception("Error handling transcription callback")

    def on_speech_error(error: str) -> None:
        logger.warning("Speech-to-text error callback", extra={"error": error})
        try:
            loop = get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    broadcaster.broadcast("error", {"error": error}), loop
                )
            else:
                loop.run_until_complete(broadcaster.broadcast("error", {"error": error}))
        except Exception:
            logger.exception("Error handling speech-to-text error callback")

    return on_speech_started, on_transcription, on_speech_error


def get_current_speech_to_text_service() -> Optional[SpeechToTextService]:
    """Return the active speech-to-text service if available."""
    return _speech_to_text_service


class SpeechToTextManager:
    """Service for speech-to-text lifecycle management."""

    def __init__(self, broadcaster: SpeechEventBroadcaster) -> None:
        self._broadcaster = broadcaster

    def start(self) -> MessageResponse:
        global _speech_to_text_service
        if SpeechToTextService is None:
            raise SpeechToTextUnavailableError(
                "Speech-to-text service is not available. Please install required "
                "dependencies: python-dotenv, deepgram-sdk, pyaudio"
            )
        if _speech_to_text_service and _speech_to_text_service.is_active:
            return MessageResponse(success=True, message="Speech-to-text is already active")
        try:
            logger.info("Creating SpeechToTextService")
            on_speech_started, on_transcription, on_speech_error = create_speech_callbacks(
                self._broadcaster
            )
            _speech_to_text_service = SpeechToTextService(
                on_speech_started=on_speech_started,
                on_transcription=on_transcription,
                on_error=on_speech_error,
            )
            logger.info("Starting speech-to-text service")
            _speech_to_text_service.start(language="fr", model="nova-2")
            logger.info(
                "Speech-to-text started",
                extra={"is_active": _speech_to_text_service.is_active},
            )
            return MessageResponse(success=True, message="Speech-to-text started")
        except Exception as exc:
            logger.exception("Failed to start speech-to-text")
            raise SpeechToTextOperationError(
                f"Failed to start speech-to-text: {exc}"
            ) from exc

    def stop(self) -> MessageResponse:
        global _speech_to_text_service
        if not _speech_to_text_service or not _speech_to_text_service.is_active:
            return MessageResponse(success=True, message="Speech-to-text is not active")
        try:
            _speech_to_text_service.stop()
            return MessageResponse(success=True, message="Speech-to-text stopped")
        except Exception as exc:
            logger.exception("Failed to stop speech-to-text")
            raise SpeechToTextOperationError(
                f"Failed to stop speech-to-text: {exc}"
            ) from exc

    def status(self) -> SpeechToTextStatusResponse:
        global _speech_to_text_service
        is_active = _speech_to_text_service is not None and _speech_to_text_service.is_active
        return SpeechToTextStatusResponse(
            is_active=is_active,
            websocket_connections=self._broadcaster.connections_count,
        )
