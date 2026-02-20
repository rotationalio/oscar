"""
Utilities for OpenTelemetry tracing and metrics.
"""

import os

from oscar.version import get_version

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


def get_service_id() -> str:
    """
    Returns pod hostname as the service ID (set by Kubernetes)
    """
    return os.environ.get("HOSTNAME", "unknown")


def get_service_name() -> str:
    """
    Returns the service name from the environment variable.
    """
    return os.environ.get("SERVICE_NAME", "oscar")


def get_traces_endpoint() -> str | None:
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", None)
    if not endpoint:
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", None)

    if endpoint is None:
        return None

    if not endpoint.endswith("/v1/traces"):
        endpoint = endpoint + "/v1/traces"
    return endpoint


def setup_opentelemetry() -> trace.Tracer:
    """
    Configures OpenTelemetry for tracing and metrics.
    """
    # Create resource identifying this service
    resource = Resource.create({
        "service.name": get_service_name(),
        "service.version": get_version(short=False),
        "service.instance": get_service_id(),
    })

    # Setup tracing
    provider = TracerProvider(resource=resource)

    # Setup exporter if configured by environment
    endpoint = get_traces_endpoint()
    if endpoint:
        exporter = OTLPSpanExporter(endpoint=get_traces_endpoint())
        provider.add_span_processor(BatchSpanProcessor(exporter))

    # Set tracer provider
    trace.set_tracer_provider(provider)

    # Instrument logging
    LoggingInstrumentor().instrument()

    return trace.get_tracer(get_service_name())
