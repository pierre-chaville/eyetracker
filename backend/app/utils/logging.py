from __future__ import annotations

import logging


def get_logger(name: str = "eyetracker.api") -> logging.Logger:
    """Return a configured logger for the API."""
    return logging.getLogger(name)
