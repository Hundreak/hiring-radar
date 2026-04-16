from __future__ import annotations

import inspect
from typing import Awaitable, Callable

from hiring_radar.services.cv_engine.batch.models import ProgressEvent

ProgressCallback = Callable[[ProgressEvent], object | Awaitable[object]]


async def emit_progress(
    callback: ProgressCallback | None,
    event: ProgressEvent,
) -> None:
    """Emit a progress event to either sync or async callback handlers."""
    if callback is None:
        return

    result = callback(event)
    if inspect.isawaitable(result):
        await result
