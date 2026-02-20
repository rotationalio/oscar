import os
import logging

from io import BytesIO
from typing import Annotated
from opentelemetry import trace
from fastapi import UploadFile, File
from oscar.models.ocr import OCRModelInfo
from fastapi.responses import ORJSONResponse
from fastapi import APIRouter, HTTPException


try:
    import docling

    from docling.datamodel.document import DoclingVersion
    from docling.datamodel.document import ConversionResult
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import DocumentStream
    from docling.datamodel.base_models import ConversionStatus
except ImportError:
    docling = None


tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/v1/docling",
    tags=["docling"],
)


@router.get("/")
async def docling_info() -> OCRModelInfo:
    if docling is None:
        raise HTTPException(status_code=501, detail="Docling is not installed")

    with tracer.start_as_current_span("docling.info"):
        info = DoclingVersion()  # type: ignore[reportOptionalMemberAccess]
        return OCRModelInfo(
            name="Docling",
            version=info.docling_version,
            description=(
                "Docling simplifies document processing, parsing diverse formats — "
                "including advanced PDF understanding — and providing seamless "
                "integrations with the generative AI ecosystem."
            ),
            url="https://docling.ai",
            repository="https://github.com/docling-project/docling",
            license="MIT",
        )


@router.post("/", response_class=ORJSONResponse)
async def docling_process(file: Annotated[UploadFile, File()]) -> ConversionResult:
    if docling is None:
        raise HTTPException(status_code=501, detail="Docling is not installed")

    with tracer.start_as_current_span("docling.process") as span:
        span.set_attribute("file.name", file.filename or "")
        span.set_attribute("file.content_type", file.content_type or "")
        span.set_attribute("file.size", file.size or 0)
        span.set_attribute("file.extension", os.path.splitext(file.filename)[1] if file.filename else "")

        # Read the file into memory
        buf = BytesIO(await file.read())
        buf.seek(0)

        name = file.filename or "file"
        converter = DocumentConverter()                         # type: ignore[reportOptionalMemberAccess]
        stream = DocumentStream(name=name, stream=buf)    # type: ignore[reportOptionalMemberAccess]
        result = converter.convert(stream)

        buf.close()

        if result.status != ConversionStatus.SUCCESS:
            raise HTTPException(status_code=500, detail=result.error)
        return result
