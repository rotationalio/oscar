from pydantic import BaseModel


class OCRModelInfo(BaseModel):
    """
    Represents information about an OCR model.
    """

    name: str
    version: str
    description: str
    url: str | None = None
    repository: str | None = None
    license: str | None = None
