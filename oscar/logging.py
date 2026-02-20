import logging
import logging.config

from pythonjsonlogger.core import RESERVED_ATTRS


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
            "()": "pythonjsonlogger.json.JsonFormatter",
            "rename_fields": {
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
            "reserved_attrs": RESERVED_ATTRS + ["color_message"],
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
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
            "filters": ["probe"],
        },
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
