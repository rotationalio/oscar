"""
Utilities for OpenTelemetry tracing, metrics, and structured logging.

This module provides:

1. JSON log formatter setup (call once at startup with configure_logging)
2. Context manager for creating manual spans with domain attributes
3. Metric instrumentation for application metrics
"""

import os
import logging

from pythonjsonlogger import json as jsonlogger


def get_service_id() -> str:
    """
    Returns pod hostname as the service ID (set by Kubernetes)
    """
    return os.environ.get("HOSTNAME", "unknown")


def configure_logging() -> None:
    """
    Configure the root logger with JSON formatter for structured output.
    Call once during FastAPI lifespan startup.

    All existing logging.getLogger(__name__) calls inherit this formatter
    automatically; there is no per-logger configuration needed.
    """
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)

    # TODO: set log level from environment variable.

    # Surpress access logs for Kubernetes probes.
    logging.getLogger("uvicorn.access").addFilter(ProbeFilter())


class ProbeFilter(logging.Filter):
    """
    Filter access logs for Kubernetes probes.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Check if the log message contains the specific endpoint path.
        message = record.getMessage()
        return (
            message.find("GET /healthz") == -1 and
            message.find("GET /livez") == -1 and
            message.find("GET /readyz") == -1
        )
