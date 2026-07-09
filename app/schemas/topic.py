from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from typing import Literal

from app.models.topic import Category
from app.models.topic import Priority
from app.models.topic import TopicStatus
from app.schemas.generation_history import GenerationHistoryRead


class TopicCreate(BaseModel):
    topic: str
    category: Category
    priority: Priority


class TopicUpdate(BaseModel):
    topic: str
    category: Category
    priority: Priority


class TopicContentUpdate(BaseModel):
    generated_post: str


class TopicRead(BaseModel):
    id: int
    topic: str
    category: Category
    priority: Priority
    status: TopicStatus
    generated_post: str | None = None
    media_asset_urn: str | None = None
    media_mime_type: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    generation_history: list["GenerationHistoryRead"] = []

    model_config = ConfigDict(from_attributes=True)


class TopicRegenerate(BaseModel):
    template_name: str = "story"
    prompt_version: str = "v1"
    generate_images: bool = False
    image_count: int = Field(default=1, ge=1, le=2)
    image_style_hint: str | None = None
    visual_template: Literal[
        "auto",
        "matrix_2x2",
        "tool_comparison",
        "flow_diagram",
        "architecture_diagram",
        "timeline",
        "checklist",
    ] = "auto"
    image_size: Literal["1024x1024", "1536x1024", "1024x1536"] = "1536x1024"
