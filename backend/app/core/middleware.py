"""
Custom Middlewares.
"""

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request and response metadata."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        # Attach request_id to request state for use in routes if needed
        request.state.request_id = request_id

        start_time = time.perf_counter()

        # Extract basic info
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        url_path = request.url.path

        logger.info(
            f"Incoming request {method} {url_path}",
            extra={"request_id": request_id, "method": method, "path": url_path, "client": client_host},
        )

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            raise exc
        finally:
            process_time = (time.perf_counter() - start_time) * 1000  # ms
            logger.info(
                f"Completed request {method} {url_path} with status {status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": url_path,
                    "status_code": status_code,
                    "duration_ms": round(process_time, 2),
                },
            )

        # Inject request ID into response headers
        response.headers["X-Request-ID"] = request_id
        return response
