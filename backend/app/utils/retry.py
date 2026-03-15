"""
Retry and timing helpers for external API calls (TTS, STT, LLM).

Uses tenacity for retries with exponential backoff; logs duration for every call.
"""
from __future__ import annotations

import logging
import time
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.settings import get_settings


def _retry_stop():
    """Return a tenacity stop condition from settings."""
    return stop_after_attempt(get_settings().retry_max_attempts)


def _retry_wait():
    s = get_settings()
    return wait_exponential(
        multiplier=1.0,
        min=s.retry_wait_min_seconds,
        max=s.retry_wait_max_seconds,
    )


async def async_with_retry_and_timing(
    logger: logging.Logger,
    operation_name: str,
    fn: Callable[..., Awaitable[T]],
    *args: object,
    transient_exceptions: tuple[type[BaseException], ...] | None = None,
    retry_if: Callable[[BaseException], bool] | None = None,
    **kwargs: object,
) -> T:
    """
    Run an async callable with retry and log duration.

    Args:
        logger: Logger for timing and retry messages.
        operation_name: Name used in log extra (e.g. "LLM generate_choices").
        fn: Async callable to run (no arguments if using transient_exceptions).
        *args: Positional arguments for fn.
        transient_exceptions: Exception types that trigger retry. Optional if retry_if set.
        retry_if: Custom predicate for retry. Optional if transient_exceptions set.
        **kwargs: Keyword arguments for fn.

    Returns:
        The return value of fn(*args, **kwargs).

    Raises:
        ValueError: If neither transient_exceptions nor retry_if is provided.
        BaseException: The last exception if all retries fail.
    """
    if retry_if is not None:
        predicate = retry_if_exception(retry_if)
    else:
        if transient_exceptions is None:
            raise ValueError("Provide transient_exceptions or retry_if")
        predicate = retry_if_exception_type(transient_exceptions)
    start = time.perf_counter()
    last_exc: BaseException | None = None
    async for attempt in AsyncRetrying(
        stop=_retry_stop(),
        wait=_retry_wait(),
        retry=predicate,
        reraise=True,
    ):
        with attempt:
            try:
                result = await fn(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info(
                    "External API call finished",
                    extra={
                        "operation": operation_name,
                        "duration_seconds": round(elapsed, 2),
                        "attempt": attempt.retry_state.attempt_number,
                    },
                )
                return result
            except BaseException as e:
                last_exc = e
                if attempt.retry_state.attempt_number < get_settings().retry_max_attempts:
                    logger.warning(
                        "External API call failed, retrying: %s (attempt %s)",
                        e,
                        attempt.retry_state.attempt_number,
                        extra={"operation": operation_name},
                    )
                raise
    raise last_exc  # type: ignore[misc]


def sync_with_retry_and_timing(
    logger: logging.Logger,
    operation_name: str,
    transient_exceptions: tuple[type[BaseException], ...],
    fn: Callable[..., T],
    *args: object,
    **kwargs: object,
) -> T:
    """
    Run a sync callable with retry and log duration.

    Args:
        logger: Logger for timing and retry messages.
        operation_name: Name used in log extra.
        transient_exceptions: Exception types that trigger retry.
        fn: Sync callable to run.
        *args: Positional arguments for fn.
        **kwargs: Keyword arguments for fn.

    Returns:
        The return value of fn(*args, **kwargs).
    """
    start = time.perf_counter()
    last_exc: BaseException | None = None
    for attempt in Retrying(
        stop=_retry_stop(),
        wait=_retry_wait(),
        retry=retry_if_exception_type(transient_exceptions),
        reraise=True,
    ):
        with attempt:
            try:
                result = fn(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info(
                    "External API call finished",
                    extra={
                        "operation": operation_name,
                        "duration_seconds": round(elapsed, 2),
                        "attempt": attempt.retry_state.attempt_number,
                    },
                )
                return result
            except transient_exceptions as e:
                last_exc = e
                if attempt.retry_state.attempt_number < get_settings().retry_max_attempts:
                    logger.warning(
                        "External API call failed, retrying: %s (attempt %s)",
                        e,
                        attempt.retry_state.attempt_number,
                        extra={"operation": operation_name},
                    )
                raise
    raise last_exc  # type: ignore[misc]
