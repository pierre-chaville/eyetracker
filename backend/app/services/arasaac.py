"""
ARASAAC pictogram lookup service.

Uses the public ARASAAC API to resolve keywords to pictogram image URLs.
API: https://api.arasaac.org/v1/pictograms/{locale}/search/{keyword}
Images: https://static.arasaac.org/pictograms/{id}/{id}_500.png
"""
from __future__ import annotations

from typing import List, Optional

import httpx

from app.utils.logging import get_logger

logger = get_logger(__name__)

_ARASAAC_API = "https://api.arasaac.org/v1/pictograms"
_ARASAAC_STATIC = "https://static.arasaac.org/pictograms"
_REQUEST_TIMEOUT = 4.0


def pictogram_image_url(pictogram_id: int) -> str:
    return f"{_ARASAAC_STATIC}/{pictogram_id}/{pictogram_id}_500.png"


async def search_pictogram(
    keyword: str,
    locale: str = "en",
    client: Optional[httpx.AsyncClient] = None,
) -> Optional[int]:
    """Search ARASAAC for a pictogram matching *keyword*. Returns the best pictogram ID or None."""
    url = f"{_ARASAAC_API}/{locale}/search/{keyword}"
    try:
        if client is not None:
            resp = await client.get(url)
        else:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as c:
                resp = await c.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data or not isinstance(data, list):
            return None
        for item in data:
            if item.get("aac"):
                return item["_id"]
        return data[0]["_id"]
    except Exception:
        logger.debug("ARASAAC search failed for keyword=%s locale=%s", keyword, locale)
        return None


async def resolve_pictogram_url(
    keywords: List[str],
    locale: str = "en",
) -> Optional[str]:
    """Try each keyword in order; return the image URL for the first match."""
    async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
        for kw in keywords:
            pid = await search_pictogram(kw.strip(), locale, client=client)
            if pid is not None:
                return pictogram_image_url(pid)
    return None
