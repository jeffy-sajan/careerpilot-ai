"""
Custom ASGI Middlewares.
Pure ASGI implementations to prevent loop-crossing bugs associated with BaseHTTPMiddleware in test environments.
"""
import logging
import time
import uuid

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware:
    """
    Pure ASGI middleware to log request and response metadata.
    Avoids Starlette's BaseHTTPMiddleware to prevent event loop mismatch errors in testing.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only process HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        
        # Attach request_id to request state scope
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id

        start_time = time.perf_counter()
        
        # Extract metadata from ASGI scope
        client = scope.get("client")
        client_host = client[0] if client else "unknown"
        method = scope.get("method", "UNKNOWN")
        url_path = scope.get("path", "")

        logger.info(
            f"Incoming request {method} {url_path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": url_path,
                "client": client_host,
            },
        )

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
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
                
                # Inject X-Request-ID into response headers
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
                
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"Completed request {method} {url_path} with status 500",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": url_path,
                    "status_code": 500,
                    "duration_ms": round(process_time, 2),
                },
            )
            raise exc
