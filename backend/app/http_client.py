"""
Shared httpx.AsyncClient for external API calls (TTS, etc.).
Set in app lifespan so one client with timeout is reused; tests can inject a mock.
"""
from __future__ import annotations

from typing import Optional

import httpx

_client: Optional[httpx.AsyncClient] = None


def set_httpx_client(client: Optional[httpx.AsyncClient]) -> None:
    """Set the shared async HTTP client (e.g. from lifespan)."""
    global _client
    _client = client


def get_httpx_client() -> Optional[httpx.AsyncClient]:
    """
    Return the shared async HTTP client if set (e.g. from lifespan).
    When None, callers should create their own client (e.g. async with httpx.AsyncClient()).
    """
    return _client
