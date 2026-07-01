"""
Schemas used by the ingestion workflow.
"""

from pydantic import BaseModel
from pydantic import Field


class IngestError(BaseModel):
    row: int
    message: str


class IngestSummary(BaseModel):
    imported: int = Field(default=0)
    duplicates: int = Field(default=0)
    failed: int = Field(default=0)

    errors: list[IngestError] = Field(default_factory=list)


class IngestRow(BaseModel):
    row: int
    topic: str
    category: str
    priority: str
    status: str
    error_message: str | None = None


class IngestResponse(BaseModel):
    success: bool
    message: str
    summary: IngestSummary
    rows: list[IngestRow] = Field(default_factory=list)