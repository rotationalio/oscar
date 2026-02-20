from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from oscar.routers import status
from oscar.version import get_version
from oscar.logging import configure_logging
from oscar.middleware import RequestLoggingMiddleware

from contextlib import asynccontextmanager


_STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager configures the service state
    """
    # Application startup
    configure_logging()
    await status.set_service_state(status.SERVICE_ONLINE)

    # Allow application to run
    yield

    # Application shutdown
    await status.set_service_state(status.SERVICE_STOPPING)


# Configure global application
app = FastAPI(
    title="Oscar",
    description="API and MCP Server for OCR Models and Text Extraction",
    version=get_version(short=True),
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# Add static files
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# Configure routers
app.include_router(status.router)


@app.get("/docs", include_in_schema=False)
async def redoc_ui_html(req: Request) -> HTMLResponse:
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Oscar API Documentation",
        redoc_favicon_url="/static/favicon.png",
    )


@app.get("/swagger", include_in_schema=False)
async def swagger_ui_html(req: Request) -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Oscar API Documentation",
        swagger_favicon_url="/static/favicon.png",
    )
