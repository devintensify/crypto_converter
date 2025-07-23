"""Middlewares for requests handling."""

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("converter_api")


class RoundtripReporterMiddleware(BaseHTTPMiddleware):
    """Http requests middleware to log roundtrip on requests processing."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Wrap request handling call into roundtrip measurement."""
        start = time.perf_counter()
        response = await call_next(request)
        duration = int((time.perf_counter() - start) * 1e3)
        log_roundtrip = f"{request.method} {request.url.path} took {duration} ms"
        logger.info(log_roundtrip)
        return response
