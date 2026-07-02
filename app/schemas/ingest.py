"""
Schemas used by the ingestion workflow.
"""

from pydantic import BaseModel
from pydantic import Field
from typing import Literal

from app.models.topic import Category
from app.models.topic import Priority


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


class TrendingNewsItem(BaseModel):
    title: str
    link: str
    source: str | None = None
    published: str | None = None


class TrendingGenerateRequest(BaseModel):
    engagement_type: Literal[
        "discussion_starter",
        "how_to_playbook",
        "trend_radar",
        "case_study_breakdown",
        "cta_to_dm",
    ] = "trend_radar"
    category: Category
    keyword: str | None = None
    priority: Priority = Priority.MEDIUM
    max_items: int = Field(default=6, ge=3, le=12)
    image_count: int = Field(default=1, ge=1, le=2)


class TrendingGenerateResponse(BaseModel):
    success: bool
    message: str
    topic_id: int
    topic: str
    engagement_type: str
    category: Category
    priority: Priority
    generated_post: str
    auto_attached_media: bool
    image_urls: list[str] = Field(default_factory=list)
    news_items: list[TrendingNewsItem] = Field(default_factory=list)