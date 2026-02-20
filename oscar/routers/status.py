import aiorwlock

from pydantic import BaseModel
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse


from oscar import __version__


# Server state constants
SERVICE_INITIALIZED = "initialized"
SERVICE_ONLINE = "ok"
SERVICE_MAINTENANCE = "maintenance"
SERVICE_STOPPING = "stopping"


router = APIRouter(
    responses={
        503: {"description": "Service Unavailable"},
    }
)

# Global variables to maintain service state and uptime.
__service_lock = aiorwlock.RWLock()
__service_state = SERVICE_INITIALIZED
__service_started = None


class Status(BaseModel):
    """
    Represents the current status of the service.
    """

    status: str
    uptime: str
    version: str = __version__
    service: str = "oscar"


@router.get("/v1/status", tags=["status"])
async def status() -> Status:
    """
    Status is an informational endpoint that returns the current version of the service,
    its service state (ok, maintenance, or stopping), as well as the uptime of the
    current instance. This information is maintained globally for fast access and
    because the service state does not change very often. Status can be used for
    heartbeats though it is preferred to use `/readyz` for that purpose.
    """
    async with __service_lock.reader_lock:
        return Status(
            status=__service_state,
            uptime=uptime(),
        )


def uptime() -> str:
    """
    Returns the uptime of the service in a human-readable format.
    """
    if __service_started is None:
        return "unknown"
    delta = datetime.now(timezone.utc) - __service_started
    return str(delta)


async def set_service_state(state: str, started: datetime | None = None) -> None:
    """
    Sets the service state and the started timestamp.
    """
    if started is None:
        started = datetime.now(timezone.utc)

    global __service_state, __service_started
    async with __service_lock.writer_lock:
        __service_state = state
        __service_started = started


@router.get("/healthz", include_in_schema=False)
async def healthz() -> PlainTextResponse:
    """
    Kubernetes probe that should always respond 200 ok if the service is running.
    This method is deprecated in favor of /livez but is included to ensure completeness
    of Kubernetes probes.
    """
    return PlainTextResponse("ok", status_code=200)


@router.get("/livez", include_in_schema=False)
async def livez() -> PlainTextResponse:
    """
    Kubernetes probe that should respond 200 ok if the service is running.
    """
    return PlainTextResponse("ok", status_code=200)


@router.get("/readyz", include_in_schema=False)
async def readyz() -> PlainTextResponse:
    """
    Kubernetes probe that should respond 200 ok if the service is ready to accept
    requests or 503 if it is not ready. This method should be updated with application
    specific readiness checks such as database connectivity, or cache availability.
    If a 200 response is returned to Kubernetes, then the Kubernetes service will send
    requests to this instance.
    """
    async with __service_lock.reader_lock:
        if __service_state != SERVICE_ONLINE:
            raise HTTPException(status_code=503, detail="Service Unavailable")
    return PlainTextResponse("ok", status_code=200)
