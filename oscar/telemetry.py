"""
Utilities for OpenTelemetry tracing and metrics.
"""

import os


def get_service_id() -> str:
    """
    Returns pod hostname as the service ID (set by Kubernetes)
    """
    return os.environ.get("HOSTNAME", "unknown")
