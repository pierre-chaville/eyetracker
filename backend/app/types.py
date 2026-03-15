"""
Shared enums and type definitions.

Uses StrEnum for string enums (event types, status codes) so they serialize
to JSON as plain strings and work in Pydantic/WebSocket payloads.
"""
from __future__ import annotations

from enum import StrEnum


class SpeechEventType(StrEnum):
    """WebSocket event types for speech-to-text and connection lifecycle."""

    CONNECTED = "connected"
    PONG = "pong"
    SPEECH_STARTED = "speech_started"
    TRANSCRIPTION = "transcription"
    ERROR = "error"
