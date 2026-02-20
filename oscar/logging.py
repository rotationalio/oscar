import os
import logging
import logging.config

import pythonjsonlogger.json as jsonlogger

from opentelemetry import trace
from pythonjsonlogger.core import RESERVED_ATTRS


def get_logging_level() -> str:
    """
    Returns the logging level based on the environment variable.
    """
    return os.environ.get("LOG_LEVEL", "INFO").upper()


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "probe": {
            "()": "oscar.logging.ProbeFilter",
        },
    },
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "()": "oscar.logging.OTelJSONFormatter",
            "reserved_attrs": RESERVED_ATTRS + ["color_message"],
            "rename_fields": {
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        },
    },
    "handlers": {
        "root": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "default": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default"],
            "level": get_logging_level(),
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": get_logging_level(),
            "propagate": False,
        },
        # Disable access logs in favor of middleware logging.
        "uvicorn.access": {
            "handlers": [],
            "level": logging.CRITICAL + 1,
            "propagate": False,
            "filters": ["probe"],
        },
    },
    "root": {
        "handlers": ["root"],
        "level": get_logging_level(),
    },
}


class ProbeFilter(logging.Filter):
    """
    Filter access logs for Kubernetes probes.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Check if the log message contains the specific endpoint path.
        message = record.getMessage()
        return (
            message.find("GET /healthz") == -1
            and message.find("GET /livez") == -1
            and message.find("GET /readyz") == -1
        )


class OTelJSONFormatter(jsonlogger.JsonFormatter):
    """
    Includes OpenTelemetry trace and span context information.
    """

    def add_fields(self, log_data: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_data, record, message_dict)

        # Add trace context if available
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            log_data["trace_id"] = format(ctx.trace_id, "032x")
            log_data["span_id"] = format(ctx.span_id, "016x")


def configure_logging() -> None:
    """
    Configure the root logger with JSON formatter for structured output.
    Call once during FastAPI lifespan startup.

    All existing logging.getLogger(__name__) calls inherit this formatter
    automatically; there is no per-logger configuration needed.
    """
    root = logging.getLogger()
    root.handlers.clear()

    logging.config.dictConfig(LOGGING_CONFIG)
