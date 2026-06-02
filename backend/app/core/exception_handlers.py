"""
Global Exception Handlers.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle all custom application exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "error_code": exc.error_code,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions."""
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Unhandled exception: %s", exc)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An internal server error occurred",
                "error_code": "INTERNAL_ERROR",
            },
        )
