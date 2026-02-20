import time
import logging
import traceback

from typing import Callable
from oscar.version import get_version
from oscar.telemetry import get_service_name

from fastapi import Request
from starlette.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


service = get_service_name()
version = get_version(short=True)
logger = logging.getLogger("oscar.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses with comprehensive error handling.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response | JSONResponse:
        started = time.perf_counter()
        method = request.method
        path = request.url.path
        if request.url.query:
            path = path + "?" + request.url.query

        try:
            # Execute the request
            response = await call_next(request)

            # Prepare the log message and extra data
            msg = f"{service} {method} {path} {response.status_code}"
            extra = {
                "service": service,
                "path": path,
                "version": version,
                "resp_time": f"{((time.perf_counter() - started) * 1000):.4f}ms",
                "method": method,
                "status": response.status_code,
            }

            # Log at the appropriate level
            if response.status_code >= 500:
                logger.error(msg, extra=extra)

            elif response.status_code >= 400:
                logger.warning(msg, extra=extra)

            elif path in {"/livez", "/healthz", "/readyz"}:
                logger.debug(msg, extra=extra)

            else:
                logger.info(msg, extra=extra)

            return response

        except Exception as e:
            # Unhandled exceptions are marked as critical since they need to be fixed.
            # The application should handle all exceptions and return a 500 response.
            logger.critical(
                f"{method} {path} - Unhandled Exception {type(e).__name__}: {str(e)}",
                extra={
                    "service": service,
                    "path": path,
                    "version": version,
                    "resp_time": f"{((time.perf_counter() - started) * 1000):.4f}ms",
                    "method": method,
                    "status": 500,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
            )

            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error"},
            )
